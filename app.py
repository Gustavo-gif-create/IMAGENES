import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

st.set_page_config(page_title="Generador de Marca y Producto", layout="wide")
st.title("📦 Generador de Fichas de Producto con Imagen de Marca")

# --- GESTIÓN DE API KEY (Secrets o Manual) ---
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API Key cargada desde Streamlit Secrets")
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key (Google AI Studio):", type="password")
    st.sidebar.markdown("""
    > **¿No tienes clave?**  
    > Consigue tu API Key gratuita en [Google AI Studio](https://aistudio.google.com/).
    > 
    > **Tip:** Puedes guardarla en *Settings -> Secrets* de Streamlit Cloud como `GEMINI_API_KEY` para no tener que ingresarla cada vez.
    """)

# --- INTERFAZ PRINCIPAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Línea de Diseño de Referencia")
    ref_image_file = st.file_uploader("Sube la imagen de estilo/marca:", type=["png", "jpg", "jpeg"])
    if ref_image_file:
        st.image(ref_image_file, caption="Estilo de Referencia", width=250)

with col2:
    st.subheader("2. Información del Producto")
    
    # Soporta múltiples archivos (PDF, PNG, JPG)
    datasheet_files = st.file_uploader(
        "Sube 1 o más datasheets / fotos (PDF, PNG, JPG):", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    # Campo para texto de modelo/marca
    product_text_info = st.text_input(
        "O ingresa Marca, Modelo o especificaciones por texto:",
        placeholder="Ej: Camara Hikvision DS-2CD2043G2-I, 4MP, visión nocturna"
    )

st.markdown("---")

# --- PROCESAMIENTO Y GENERACIÓN ---
if st.button("🚀 Analizar y Generar Imagen", type="primary"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key de Gemini en el panel izquierdo o en los Secrets.")
    elif not ref_image_file:
        st.warning("Debes subir al menos la imagen de referencia de tu marca.")
    elif not datasheet_files and not product_text_info.strip():
        st.warning("Debes subir al menos un archivo (PDF/Imagen) O escribir la marca/modelo del producto.")
    else:
        with st.spinner("Analizando datos y procesando con IA..."):
            try:
                # 1. Configurar la clave de la API limpiando comillas o espacios extras
                clean_api_key = str(api_key).strip().strip('"').strip("'")
                genai.configure(api_key=clean_api_key)
                
                # Lista de contenidos que procesará la IA
                contents = []
                
                # 2. Procesar imagen de referencia de marca
                img_ref = Image.open(ref_image_file)
                contents.append(img_ref)

                # 3. Procesar los archivos adjuntos (PDFs e Imágenes)
                if datasheet_files:
                    for uploaded_file in datasheet_files:
                        bytes_data = uploaded_file.getvalue()
                        mime_type = uploaded_file.type
                        
                        # Empaquetado binario estándar
                        contents.append({
                            "mime_type": mime_type,
                            "data": bytes_data
                        })

                # 4. Construir las instrucciones para la IA
                prompt_analisis = f"""
                Analiza los elementos adjuntos:
                1. La primera imagen es la REFERENCIA DE ESTILO VISUAL DE MARCA (analiza fondo, paleta de colores, iluminación, composición y estética general).
                2. Los archivos adjuntos en PDF/imágenes o el siguiente texto corresponden al PRODUCTO O DATASHEET.
                
                Información del producto en texto: "{product_text_info}"

                INSTRUCCIONES:
                - Extrae qué producto es, su forma física, colores principales y sus 3 características técnicas más importantes.
                - Redacta un PROMPT TÉCNICO Y DETALLADO EN INGLÉS optimizado para generadores de imágenes (ej. Flux/Stable Diffusion).
                - El prompt debe describir la recreación fotográfica fotorrealista del producto integrado de forma armónica dentro del entorno, iluminación y fondo de la IMAGEN DE REFERENCIA DE MARCA.
                - Pide explícitamente que la imagen muestre una estética limpia de catálogo/banner publicitario.

                REGLA ESTRICTA: Devuelve ÚNICAMENTE el prompt final en inglés, sin explicaciones ni formato markdown adicional.
                """

                contents.append(prompt_analisis)

                # 5. Inicializar el modelo con el nombre estándar universalmente soportado
                model = genai.GenerativeModel('gemini-1.5-flash-latest')

                # Llamada de generación de texto/análisis
                response = model.generate_content(contents)
                final_prompt = response.text.strip()
                
                st.success("Análisis de información completado exitosamente.")
                with st.expander("Ver el Prompt técnico generado por la IA"):
                    st.write(final_prompt)

                # 6. Generación de la imagen publicitaria final con Pollinations (Flux)
                with st.spinner("Dibujando la imagen final con la estética de tu marca..."):
                    encoded_prompt = urllib.parse.quote(final_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
                    
                    st.markdown("### 🎨 Resultado Final")
                    st.image(image_url, caption="Imagen generada con la línea de diseño de tu marca", use_container_width=True)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la solicitud: {e}")
