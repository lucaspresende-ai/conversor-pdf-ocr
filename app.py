import streamlit as st
import os
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import io
import img2pdf

st.set_page_config(
    page_title="Conversor PDF para OCR",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Conversor de PDF para PDF com Texto Selecionável")
st.markdown("### Transforme PDFs escaneados em PDFs com texto pesquisável usando OCR")

# Instruções
with st.expander("ℹ️ Como usar esta aplicação"):
    st.markdown("""
    1. **Faça upload** do seu arquivo PDF (até 1GB)
    2. **Aguarde** o processamento automático
    3. **Baixe** o PDF convertido com texto selecionável
    
    **Nota:** Arquivos maiores podem levar alguns minutos para processar.
    """)

# Upload do arquivo
uploaded_file = st.file_uploader(
    "Escolha seu arquivo PDF",
    type=['pdf'],
    help="Carregue um arquivo PDF de até 1GB"
)

if uploaded_file is not None:
    # Mostra informações do arquivo
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.info(f"📊 Arquivo carregado: {uploaded_file.name} ({file_size_mb:.2f} MB)")
    
    # Botão para processar
    if st.button("🚀 Processar PDF", type="primary"):
        try:
            with st.spinner("⏳ Processando PDF... Isso pode levar alguns minutos para arquivos grandes."):
                # Converte PDF para imagens
                st.write("📷 Convertendo PDF para imagens...")
                images = convert_from_bytes(
                    uploaded_file.getvalue(),
                    dpi=200,  # Qualidade razoável
                    fmt='jpeg'
                )
                
                # Cria barra de progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Lista para armazenar imagens processadas
                processed_images = []
                
                # Processa cada página
                total_pages = len(images)
                for idx, image in enumerate(images):
                    status_text.text(f"🔍 Executando OCR na página {idx + 1} de {total_pages}...")
                    
                    # Converte imagem PIL para bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG', quality=85)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    processed_images.append(img_byte_arr)
                    
                    # Atualiza barra de progresso
                    progress_bar.progress((idx + 1) / total_pages)
                
                # Cria PDF com OCR
                status_text.text("📝 Gerando PDF final com texto selecionável...")
                
                # Converte imagens para PDF
                pdf_bytes = img2pdf.convert(processed_images)
                
                # Limpa status
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Processamento concluído com sucesso!")
                
                # Botão de download
                st.download_button(
                    label="⬇️ Baixar PDF com OCR",
                    data=pdf_bytes,
                    file_name=f"ocr_{uploaded_file.name}",
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.info("💡 Dica: Verifique se o arquivo é um PDF válido.")

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    <small>Desenvolvido com Streamlit 🎈 | OCR com Tesseract</small>
    </div>
    """,
    unsafe_allow_html=True
)
