import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import urllib.parse
import io

st.set_page_config(page_title="Generador de Marca y Producto", layout="wide")
st.title("📦 Generador de Fichas de Producto con Imagen de Marca")

# Configurar API Key
api_key = st.sidebar.text_input("Ingresa tu Gemini API Key (Google AI Studio):", type="password")

st.sidebar.markdown("""
> **Consigue tu API Key gratuita en:**  
> [Google AI Studio](https://aistudio.google.com/)
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Línea de Diseño de Referencia")
    ref_image_file = st.file_uploader("Sube la imagen de estilo/marca:", type=["png", "jpg", "jpeg"])
    if ref_image_file:
        st.image(ref_image_file, caption="Estilo de Referencia", width=250)

with col2:
    st.subheader("2. Información del Producto")
    
    # Opción A: Archivos (Soporta múltiples archivos: PDF, PNG, JPG)
    datasheet_files = st.file_uploader(
        "Sube 1 o más datasheets / fotos (PDF, PNG, JPG):", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    # Opción B: Modelo, Marca o Búsqueda por texto
    product_text_info = st.text_input(
        "O ingresa Marca, Modelo o información del producto:",
        placeholder="Ej: Camara Hikvision DS-2CD2043G2-I, 4MP, visión nocturna"
    )

st.markdown("---")

if st.button("🚀 Analizar y Generar Imagen"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key de Gemini en el panel izquierdo.")
    elif not ref_image_file:
        st.warning("Debes subir al menos la imagen de referencia de tu marca.")
    elif not datasheet_files and not product_text_info:
        st.warning("Debes subir al menos un archivo (PDF/Imagen) O ingresar la marca/modelo en texto.")
    else:
        with st.spinner("Analizando información y estilo con IA..."):
            try:
                client = genai.Client(api_key=api_key)
                
                # Lista de contenidos que enviaremos a Gemini
                contents = []
                
                # 1. Agregar la imagen de referencia visual
                img_ref = Image.open(ref_image_file)
                contents.append(img_ref)

                # 2. Agregar los archivos adjuntos (PDFs o imágenes)
                if datasheet_files:
                    for uploaded_file in datasheet_files:
                        bytes_data = uploaded_file.read()
                        mime_type = uploaded_file.type
                        
                        # Si es PDF o Imagen, pasarlo en el formato compatible con google-genai
                        contents.append(
                            types.Part.from_bytes(
                                data=bytes_data,
                                mime_type=mime_type
                            )
                        )

                # 3. Construir el prompt de análisis
                prompt_analisis = f"""
                Analiza los archivos adjuntos:
                - La primera imagen proporcionada es el ESTILO VISUAL DE MARCA (colores, iluminación, fondo, composición y estética general).
                - El resto de los archivos (PDFs/Imágenes) contienen el PRODUCTO o DATASHEET.
                
                Información adicional / Marca y Modelo ingresada por texto: "{product_text_info}"

                TAREA:
                1. Extrae qué producto es, su forma, color y sus 3 a 5 características principales.
                2. Si hay una marca/modelo especificada o detectada en el datasheet, busca/revisa sus especificaciones clave.
                3. Crea un 'prompt' detallado en INGLES para un modelo de generación de imágenes que recree el producto, 
                   integrado dentro del entorno, fondo, iluminación y estilo visual de la imagen de referencia de marca.
                4. Especifica que la imagen resultante incluya texto elegante o elementos visuales limpios con las características principales.
                
                Devuelve ÚNICAMENTE el prompt final en inglés, sin explicaciones ni introducciones.
                """

                contents.append(prompt_analisis)

                # Llamada a Gemini (Soporta PDFs e imágenes nativamente)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents
                )
                
                final_prompt = response.text.strip()
                st.success("Análisis completado exitosamente.")
                st.write("**Prompt técnico generado:**", final_prompt)

                # Generar Imagen con Pollinations.ai (Flux)
                with st.spinner("Generando la nueva imagen de producto..."):
                    encoded_prompt = urllib.parse.quote(final_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
                    
                    st.markdown("### 🎨 Resultado Final")
                    st.image(image_url, caption="Imagen generada con la línea de diseño de tu marca", use_column_width=True)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la solicitud: {e}")
