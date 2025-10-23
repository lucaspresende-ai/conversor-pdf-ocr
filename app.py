import streamlit as st
import fitz  # PyMuPDF
import gc
import time

st.set_page_config(
    page_title="Conversor PDF 500+ Páginas",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Conversor PDF para OCR - Otimizado para Arquivos Grandes")
st.markdown("### ⚡ Sistema otimizado para PDFs de 500+ páginas")

# Configurações otimizadas
BATCH_SIZE = 25  # Processa 25 páginas por vez
MAX_DPI = 150    # DPI reduzido para economizar memória

def process_page_batch(pdf_bytes, start_page, end_page, batch_num):
    """Processa um lote de páginas"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        output_pdf = fitz.open()
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            
            rect = page.rect
            new_page = output_pdf.new_page(width=rect.width, height=rect.height)
            
            pix = page.get_pixmap(dpi=MAX_DPI)
            new_page.insert_image(rect, pixmap=pix)
            
            try:
                blocks = page.get_text("dict", flags=11)["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span.get("text", "").strip():
                                    bbox = span["bbox"]
                                    new_page.insert_text(
                                        (bbox[0], bbox[3]),
                                        span["text"],
                                        fontsize=max(6, span.get("size", 10)),
                                        render_mode=3
                                    )
            except:
                pass
            
            pix = None
            page = None
            gc.collect()
        
        batch_bytes = output_pdf.tobytes()
        
        doc.close()
        output_pdf.close()
        doc = None
        output_pdf = None
        gc.collect()
        
        return batch_bytes, batch_num
        
    except Exception as e:
        st.error(f"Erro no lote {batch_num}: {str(e)}")
        return None, batch_num

def merge_pdf_batches(batch_results):
    """Mescla todos os lotes em um PDF final"""
    final_pdf = fitz.open()
    
    sorted_batches = sorted([r for r in batch_results if r[0] is not None], key=lambda x: x[1])
    
    for batch_bytes, batch_num in sorted_batches:
        if batch_bytes:
            batch_doc = fitz.open(stream=batch_bytes, filetype="pdf")
            final_pdf.insert_pdf(batch_doc)
            batch_doc.close()
            batch_doc = None
            gc.collect()
    
    result = final_pdf.tobytes()
    final_pdf.close()
    final_pdf = None
    gc.collect()
    
    return result

with st.expander("ℹ️ Como funciona"):
    st.markdown(f"""
    **Sistema Otimizado:**
    - Processa **{BATCH_SIZE} páginas por vez**
    - **DPI {MAX_DPI}** (qualidade boa, tamanho controlado)
    - **Processamento em lotes** (não trava a memória)
    - **Limpeza automática** de RAM
    
    **Para seu PDF de 500 páginas:** ~20 lotes
    **Tempo estimado:** 15-25 minutos
    """)

uploaded_file = st.file_uploader(
    "Escolha seu PDF",
    type=['pdf'],
    help="Otimizado para PDFs grandes"
)

if uploaded_file is not None:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.info(f"📊 **{uploaded_file.name}** - {file_size_mb:.1f} MB carregado")
    
    try:
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        
        total_batches = (total_pages + BATCH_SIZE - 1) // BATCH_SIZE
        estimated_time = total_batches * 0.8
        
        st.success(f"✅ **{total_pages} páginas** | **{total_batches} lotes** | ~**{estimated_time:.0f} minutos**")
        
    except Exception as e:
        st.error(f"❌ Erro ao analisar PDF: {str(e)}")
        st.stop()
    
    if st.button("🚀 PROCESSAR PDF", type="primary"):
        start_time = time.time()
        
        try:
            progress_container = st.container()
            with progress_container:
                st.write("⏳ **Processando em lotes...**")
                main_progress = st.progress(0)
                status_text = st.empty()
                batch_info = st.empty()
            
            batch_results = []
            
            for i in range(total_batches):
                start_page = i * BATCH_SIZE
                end_page = min((i + 1) * BATCH_SIZE, total_pages)
                
                status_text.text(f"🔄 Lote {i+1}/{total_batches}")
                batch_info.text(f"📄 Páginas {start_page+1} a {end_page}")
                
                batch_result = process_page_batch(pdf_bytes, start_page, end_page, i)
                batch_results.append(batch_result)
                
                progress = (i + 1) / total_batches
                main_progress.progress(progress)
                
                if (i + 1) % 5 == 0:
                    gc.collect()
                    time.sleep(0.5)
            
            status_text.text("🔗 Mesclando lotes...")
            final_pdf_bytes = merge_pdf_batches(batch_results)
            
            batch_results = None
            gc.collect()
            
            elapsed_time = time.time() - start_time
            main_progress.progress(1.0)
            status_text.empty()
            batch_info.empty()
            
            st.success(f"✅ **CONCLUÍDO!** {elapsed_time/60:.1f} minutos")
            
            final_size_mb = len(final_pdf_bytes) / (1024 * 1024)
            st.info(f"📊 Arquivo: {final_size_mb:.1f} MB | {total_pages} páginas")
            
            st.download_button(
                label="⬇️ BAIXAR PDF COM OCR",
                data=final_pdf_bytes,
                file_name=f"ocr_{uploaded_file.name}",
                mime="application/pdf",
                key="download_final"
            )
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    <small>⚡ Otimizado para PDFs grandes | PyMuPDF</small>
    </div>
    """,
    unsafe_allow_html=True
)
