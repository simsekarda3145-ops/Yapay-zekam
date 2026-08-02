import torch
from diffusers import StableDiffusionPipeline
import gradio as gr

# 1. Yapay Zeka Modelini Yükleme
model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
if torch.cuda.is_available():
    pipe = pipe.to("cuda")

# 2. Resim Oluşturma Fonksiyonu (Pekmez Kontrolü Burada!)
def resim_olustur(prompt):
    # Kullanıcı "pekmez" yazdıysa API/Model çalışmaz, direkt senin resmin döner
    if "pekmez" in prompt.lower():
        return "pekmez.jpg"
    
    # "Pekmez" dışında bir şey yazıldıysa Yapay Zeka devreye girer
    image = pipe(prompt).images[0]
    return image

# 3. Arayüz Mantığı (Gradio)
demo = gr.Interface(
    fn=resim_olustur,
    inputs=gr.Textbox(label="Ne çizmek istersin?"),
    outputs=gr.Image(label="Sonuç"),
    title="Yapay Zeka Görsel Oluşturucu"
)

# Uygulamayı Başlat
if __name__ == "__main__":
    demo.launch()
