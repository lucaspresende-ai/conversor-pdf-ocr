import streamlit as st
import fitz
import gc
import time

st.set_page_config(
    page_title="Conversor PDF OCR",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Conversor PDF para OCR")
st.markdown("### ⚡ Otimizado para PDFs grandes")

BATCH_SIZE = 20
MAX_DPI = 100

def process_page_batch(pdf_bytes, start_page, end_page, batch_num):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        output_pdf = fitz.open()
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            rect = page.rect
            new_page = output_pdf.new_page(width=rect.width, height=rect.height)
            
            try:
                pix = page.get_pixmap(dpi=MAX_DPI)
                new_page.insert_image(rect, pixmap=pix)
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
        return None, batch_num

def merge_pdf_batches(batch_results):
    final_pdf = fitz.open()
    
    sorted_batches = sorted([r for r in batch_results if r[0] is not None], key=lambda x: x[1])
    
    for batch_bytes, batch_num in sorted_batches:
        if batch_bytes:
            try:
                batch_doc = fitz.open(stream=batch_bytes, filetype="pdf")
                final_pdf.insert_pdf(batch_doc)
                batch_doc.close()
                batch_doc = None
                gc.collect()
            except:
                pass
    
    result = final_pdf.tobytes()
    final_pdf.close()
    final_pdf = None
    gc.collect()
    
    return result

uploaded_file = st.file_uploader("Escolha seu PDF", type=['pdf'])

if uploaded_file is not None:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.info(f"📊 {uploaded_file.name} - {file_size_mb:.1f} MB")
    
    try:
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        
        total_batches = (total_pages + BATCH_SIZE - 1) // BATCH_SIZE
        st.success(f"✅ {total_pages} páginas | {total_batches} lotes")
        
    except Exception as e:
        st.error(f"❌ Erro ao analisar: {str(e)}")
        st.stop()
    
    if st.button("🚀 PROCESSAR", type="primary"):
        start_time = time.time()
        
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            batch_results = []
            
            for i in range(total_batches):
                start_page = i * BATCH_SIZE
                end_page = min((i + 1) * BATCH_SIZE, total_pages)
                
                status_text.text(f"Lote {i+1}/{total_batches}")
                
                batch_result = process_page_batch(pdf_bytes, start_page, end_page, i)
                batch_results.append(batch_result)
                
                progress_bar.progress((i + 1) / total_batches)
                
                if (i + 1) % 3 == 0:
                    gc.collect()
                    time.sleep(0.2)
            
            status_text.text("Finalizando...")
            final_pdf_bytes = merge_pdf_batches(batch_results)
            
            batch_results = None
            gc.collect()
            
            elapsed_time = time.time() - start_time
            progress_bar.progress(1.0)
            status_text.empty()
            
            st.success(f"✅ Concluído em {elapsed_time/60:.1f} minutos!")
            
            final_size_mb = len(final_pdf_bytes) / (1024 * 1024)
            
            st.download_button(
                label="⬇️ Baixar PDF",
                data=final_pdf_bytes,
                file_name=f"ocr_{uploaded_file.name}",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error
