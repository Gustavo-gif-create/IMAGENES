import streamlit as st
from google import genai
from PIL import Image
import urllib.parse
import io

st.set_page_config(page_title="Generador de Marca y Producto", layout="wide")
st.title("📦 Generador de Fichas de Producto con Imagen de Marca")

# 1. Configurar clave de API de Gemini (Gratuita)
api_key = st.sidebar.text_input("Ingresa tu Gemini API Key (Google AI Studio):", type="password")

st.sidebar.markdown("""
> **¿Dónde conseguir la API Key gratuita?**  
> Ve a [Google AI Studio](https://aistudio.google.com/), crea una API key gratuita y pégala arriba.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Línea de Diseño de Referencia")
    ref_image_file = st.file_uploader("Sube una imagen de ejemplo (Estilo de tu marca):", type=["png", "jpg", "jpeg"])
    if ref_image_file:
        st.image(ref_image_file, caption="Estilo de Referencia", width=250)

with col2:
    st.subheader("2. Producto / Datasheet")
    datasheet_file = st.file_uploader("Sube la imagen del producto o datasheet:", type=["png", "jpg", "jpeg"])
    if datasheet_file:
        st.image(datasheet_file, caption="Producto / Datasheet", width=250)

st.markdown("---")

if st.button("🚀 Analizar y Generar Imagen"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key de Gemini en el panel izquierdo.")
    elif not ref_image_file or not datasheet_file:
        st.warning("Debes subir tanto la imagen de referencia como el datasheet o producto.")
    else:
        with st.spinner("Analizando datasheet y estilo con IA..."):
            try:
                client = genai.Client(api_key=api_key)
                
                # Cargar imágenes con PIL
                img_ref = Image.open(ref_image_file)
                img_data = Image.open(datasheet_file)

                # Prompt para extraer estilo y características
                prompt_analisis = """
                Analiza las dos imágenes adjuntas:
                1. La primera imagen es el ESTILO VISUAL DE MARCA (analiza los colores, iluminación, fondo, composición y estética general).
                2. La segunda imagen es el PRODUCTO o DATASHEET (extrae qué producto es, su forma, color y sus 3 características principales).

                Crea un 'prompt' detallado en INGLES para un modelo de generación de imágenes que recree el producto de la segunda imagen, 
                pero integrado completamente dentro del entorno, fondo, iluminación y estilo visual de la primera imagen.
                Incluye en la descripción del prompt que se muestren de forma gráfica o con texto elegante las características clave del producto.
                Devuelve ÚNICAMENTE el prompt en inglés sin introducciones ni comentarios.
                """

                # Llamada a Gemini 2.5 Flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[img_ref, img_data, prompt_analisis]
                )
                
                final_prompt = response.text.strip()
                st.success("Análisis de visión completado.")
                st.write("**Prompt generado para el modelo:**", final_prompt)

                # Generación de la Imagen Final vía Pollinations.ai
                with st.spinner("Generando nueva imagen con el estilo de tu marca..."):
                    encoded_prompt = urllib.parse.quote(final_prompt)
                    # Forzamos alta definición y modelo flux
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
                    
                    st.markdown("### 🎨 Resultado Final")
                    st.image(image_url, caption="Producto generado con la línea visual de tu marca", use_column_width=True)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
