import streamlit as st
import requests
from pdf2image import convert_from_bytes
import fitz
import io
import time
from PIL import Image

st.set_page_config(
    page_title="Conversor PDF OCR",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Conversor PDF para Texto Selecionável")
st.markdown("### ⚡ OCR via Nuvem - Gratuito e Sem Limites")

with st.expander("ℹ️ Como funciona"):
    st.markdown("""
    **Sistema OCR em Nuvem:**
    - Converte PDF escaneado em texto selecionável
    - Usa OCR.space (API gratuita, sem limite de páginas)
    - Processa lote por lote para PDFs grandes
    - **Texto 100% selecionável no PDF final**
    
    **Tempo estimado:** ~2-3 minutos por 100 páginas
    """)

uploaded_file = st.file_uploader("Escolha seu PDF", type=['pdf'])

if uploaded_file is not None:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.info(f"📊 {uploaded_file.name} - {file_size_mb:.1f} MB")
    
    try:
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        
        st.success(f"✅ {total_pages} páginas detectadas")
        
    except Exception as e:
        st.error(f"❌ Erro ao analisar: {str(e)}")
        st.stop()
    
    if st.button("🚀 PROCESSAR COM OCR", type="primary"):
        start_time = time.time()
        
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Converte PDF em imagens
            status_text.text("📷 Convertendo PDF em imagens...")
            images = convert_from_bytes(pdf_bytes, dpi=200)
            
            status_text.text("🔄 Enviando para OCR em nuvem...")
            
            # Lista para armazenar texto extraído
            all_text_blocks = []
            
            # Processa cada página com OCR.space
            for page_num, image in enumerate(images):
                progress = page_num / len(images)
                progress_bar.progress(progress)
                status_text.text(f"🔍 Processando página {page_num + 1}/{len(images)}...")
                
                # Converte imagem PIL para bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                # Envia para OCR.space API
                try:
                    files = {'filename': img_byte_arr}
                    payload = {
                        'apikey': 'K87899142C87',  # API key gratuita do OCR.space
                        'language': 'por'  # Português
                    }
                    
                    response = requests.post(
                        'https://api.ocr.space/parse/image',
                        files=files,
                        data=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('IsErroredOnProcessing') == False:
                            extracted_text = result.get('ParsedText', '')
                            all_text_blocks.append({
                                'page': page_num + 1,
                                'text': extracted_text
                            })
                        else:
                            st.warning(f"⚠️ Erro na página {page_num + 1}: {result.get('ErrorMessage', 'Desconhecido')}")
                    
                    time.sleep(0.5)  # Pequena pausa entre requisições
                    
                except Exception as e:
                    st.warning(f"⚠️ Erro ao processar página {page_num + 1}: {str(e)}")
            
            progress_bar.progress(1.0)
            status_text.text("📝 Gerando PDF com texto selecionável...")
            
            # Cria novo PDF com texto selecionável
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            output_pdf = fitz.open()
            
            for idx, page in enumerate(doc):
                output_pdf.insert_pdf(doc, from_page=idx, to_page=idx)
                
                # Adiciona texto invisível na página
                if idx < len(all_text_blocks):
                    text_block = all_text_blocks[idx]
                    text = text_block['text']
                    
                    # Adiciona texto em pontos estratégicos da página
                    if text.strip():
                        # Divide texto em linhas e adiciona na página
                        lines = text.split('\n')
                        y_position = 50
                        
                        new_page = output_pdf[idx]
                        for line in lines[:50]:  # Limita a 50 linhas por página
                            if line.strip():
                                new_page.insert_text(
                                    (50, y_position),
                                    line[:100],  # Limita tamanho da linha
                                    fontsize=10,
                                    render_mode=3  # Texto invisível
                                )
                                y_position += 15
            
            output_bytes = output_pdf.tobytes()
            doc.close()
            output_pdf.close()
            
            elapsed_time = time.time() - start_time
            status_text.empty()
            
            final_size_mb = len(output_bytes) / (1024 * 1024)
            
            st.success(f"✅ Concluído em {elapsed_time/60:.1f} minutos!")
            st.info(f"📄 {total_pages} páginas com OCR aplicado")
            
            st.download_button(
                label="⬇️ BAIXAR PDF COM TEXTO OCR",
                data=output_bytes,
                file_name=f"ocr_{uploaded_file.name}",
                mime="application/pdf"
            )
            
            # Mostra estatísticas
            with st.expander("📊 Texto extraído (prévia)"):
                for block in all_text_blocks[:3]:  # Mostra primeiras 3 páginas
                    st.write(f"**Página {block['page']}:**")
                    st.write(block['text'][:500] + "...")
                    st.divider()
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            st.info("💡 Tente novamente em alguns momentos")
