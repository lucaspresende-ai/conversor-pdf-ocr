import streamlit as st
import requests
import fitz
import io
import time

st.set_page_config(
    page_title="Conversor PDF OCR",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Conversor PDF para Texto Selecionável")
st.markdown("### ⚡ OCR via Nuvem - Sem Poppler")

with st.expander("ℹ️ Como funciona"):
    st.markdown("""
    **Sistema OCR em Nuvem:**
    - Converte PDF escaneado em texto selecionável
    - Usa OCR.space (API gratuita)
    - **Sem dependências externas complexas**
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
            
            # Abre PDF e converte em imagens usando PyMuPDF (sem Poppler)
            status_text.text("📷 Convertendo PDF em imagens...")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            all_text_blocks = []
            
            # Processa cada página
            for page_num in range(total_pages):
                progress = page_num / total_pages
                progress_bar.progress(progress)
                status_text.text(f"🔍 Processando página {page_num + 1}/{total_pages}...")
                
                try:
                    # Renderiza página como imagem usando PyMuPDF
                    page = doc[page_num]
                    pix = page.get_pixmap(dpi=200, alpha=False)
                    
                    # Converte para PNG em memória
                    img_bytes = pix.tobytes("png")
                    img_data = io.BytesIO(img_bytes)
                    
                    # Envia para OCR.space API
                    files = {'filename': img_data}
                    payload = {
                        'apikey': 'K87899142C87',
                        'language': 'por'
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
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    st.warning(f"⚠️ Erro página {page_num + 1}: {str(e)}")
            
            doc.close()
            
            progress_bar.progress(0.95)
            status_text.text("📝 Gerando PDF com texto selecionável...")
            
            # Cria novo PDF com texto extraído
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            output_pdf = fitz.open()
            
            for idx in range(total_pages):
                # Copia página original
                output_pdf.insert_pdf(doc, from_page=idx, to_page=idx)
                
                # Adiciona texto extraído como camada invisível
                if idx < len(all_text_blocks):
                    text_block = all_text_blocks[idx]
                    text = text_block['text']
                    
                    if text.strip():
                        new_page = output_pdf[idx]
                        
                        # Adiciona texto invisível para busca/seleção
                        lines = text.split('\n')
                        y_pos = 30
                        
                        for line in lines[:80]:
                            if line.strip() and len(line.strip()) > 0:
                                try:
                                    new_page.insert_text(
                                        (20, y_pos),
                                        line[:150],
                                        fontsize=8,
                                        render_mode=3,
                                        color=(1, 1, 1),
                                        opacity=0
                                    )
                                    y_pos += 12
                                except:
                                    pass
            
            output_bytes = output_pdf.tobytes()
            doc.close()
            output_pdf.close()
            
            elapsed_time = time.time() - start_time
            progress_bar.progress(1.0)
            status_text.empty()
            
            final_size_mb = len(output_bytes) / (1024 * 1024)
            
            st.success(f"✅ Concluído em {elapsed_time/60:.1f} minutos!")
            st.info(f"📄 {total_pages} páginas com OCR aplicado | {final_size_mb:.1f} MB")
            
            st.download_button(
                label="⬇️ BAIXAR PDF COM TEXTO OCR",
                data=output_bytes,
                file_name=f"ocr_{uploaded_file.name}",
                mime="application/pdf"
            )
            
            with st.expander("📊 Texto extraído (prévia das 3 primeiras)"):
                for block in all_text_blocks[:3]:
                    st.write(f"**Página {block['page']}:**")
                    preview_text = block['text'][:400] if block['text'] else "(sem texto)"
                    st.write(preview_text + "...")
                    st.divider()
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            st.info("💡 Verifique se o PDF é válido e tente novamente")
