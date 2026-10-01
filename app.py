import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import urllib.parse

st.set_page_config(page_title="Generador de Marca y Producto", layout="wide")
st.title("📦 Generador de Fichas de Producto con Imagen de Marca")

# --- GESTIÓN DE API KEY ---
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API Key cargada desde Streamlit Secrets")
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key (Google AI Studio):", type="password")

# --- INTERFAZ PRINCIPAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Línea de Diseño de Referencia")
    ref_image_file = st.file_uploader("Sube la imagen de estilo/marca:", type=["png", "jpg", "jpeg"])
    if ref_image_file:
        st.image(ref_image_file, caption="Estilo de Referencia", width=250)

with col2:
    st.subheader("2. Información del Producto")
    datasheet_files = st.file_uploader(
        "Sube 1 o más datasheets / fotos (PDF, PNG, JPG):", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    product_text_info = st.text_input(
        "O ingresa Marca, Modelo o especificaciones por texto:",
        placeholder="Ej: Camara Hikvision DS-2CD2043G2-I, 4MP, visión nocturna"
    )

st.markdown("---")

# --- PROCESAMIENTO Y GENERACIÓN ---
if st.button("🚀 Analizar y Generar Imagen", type="primary"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key de Gemini.")
    elif not ref_image_file:
        st.warning("Debes subir la imagen de referencia de tu marca.")
    elif not datasheet_files and not product_text_info.strip():
        st.warning("Debes subir un archivo O escribir la marca/modelo del producto.")
    else:
        with st.spinner("Analizando datos y procesando con IA..."):
            try:
                # Limpiar clave de la API
                clean_api_key = str(api_key).strip().strip('"').strip("'")
                client = genai.Client(api_key=clean_api_key)
                
                contents = []
                
                # 1. Convertir y agregar imagen de referencia
                img_ref = Image.open(ref_image_file)
                contents.append(img_ref)

                # 2. Agregar archivos adjuntos (PDFs o imágenes)
                if datasheet_files:
                    for uploaded_file in datasheet_files:
                        bytes_data = uploaded_file.getvalue()
                        mime_type = uploaded_file.type
                        contents.append(
                            types.Part.from_bytes(
                                data=bytes_data,
                                mime_type=mime_type
                            )
                        )

                # 3. Prompt de instrucción para el análisis
                prompt_analisis = f"""
                Analiza los elementos adjuntos:
                1. La primera imagen es la REFERENCIA DEL ESTILO VISUAL DE LA MARCA (fondo, colores, iluminación).
                2. Los archivos adjuntos o texto son las especificaciones técnicas/fotos del PRODUCTO.
                
                Texto del producto: "{product_text_info}"

                INSTRUCCIONES:
                - Identifica el producto, sus materiales/forma y sus 3 características principales.
                - Genera un PROMPT TÉCNICO EN INGLÉS detallado para un generador de imágenes fotorrealistas (Flux/Stable Diffusion).
                - El prompt debe indicar que se recree el producto perfectamente integrado en el estilo visual, iluminación y paleta de colores de la imagen de referencia de marca.

                REGLA: Devuelve ÚNICAMENTE el prompt final en inglés, sin encabezados ni explicaciones adicionales.
                """
                contents.append(prompt_analisis)

                # Lista de fallback para modelos estables y vigentes
                model_names = ['gemini-2.5-flash', 'gemini-1.5-flash']
                response = None
                last_error = None

                for model_name in model_names:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents
                        )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_error = err
                        continue

                if not response or not response.text:
                    raise Exception(f"No se pudo completar con los modelos disponibles: {last_error}")

                final_prompt = response.text.strip()
                
                st.success("Análisis completado exitosamente.")
                with st.expander("Ver el Prompt técnico generado"):
                    st.write(final_prompt)

                # Generación de la imagen publicitaria
                with st.spinner("Generando imagen publicitaria..."):
                    encoded_prompt = urllib.parse.quote(final_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
                    
                    st.markdown("### 🎨 Resultado Final")
                    st.image(image_url, caption="Imagen generada con la línea de diseño de tu marca", use_container_width=True)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la solicitud: {e}")
