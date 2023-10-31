from django.http import HttpResponse
from django.template import loader
from requests import post,get


ruta = "http://127.0.0.1:5000"
def getInfo(request):
    return HttpResponse("Frontend: Estudiante de ipc3")

def index(request):
    template = loader.get_template('Index.html')
    return HttpResponse(template.render())
def leerArchivo(request):
    template = loader.get_template('Lectura_mensajes.html')
    return HttpResponse(template.render())
def reporte (request):

    url = "http://127.0.0.1:3050/api"
    rsp = get(url)
    print(rsp.json())
    existe = False
    nombre_reporte = "Sentimiento de mensajes"
    descripcion = "Reporte de sentimiento de mensajes"
    conte = [10,20,30]
    template = loader.get_template('reporte.html')
    return HttpResponse(template.render({'exist':existe,'nombre_reporte':nombre_reporte,'descripcion':descripcion,'conte':conte, 'repuesta':rsp.json()},request))



def cargar_archivo_django(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')

        if archivo:
            # Crear una solicitud POST al backend de Flask
            url_flask = ruta+'/grabarMensajes'
            files = {'archivo': archivo}
            response = request.post(url_flask, files=files)

            if response.status_code == 200:
                return HttpResponse('Archivo cargado con éxito en Flask')
            else:
                return HttpResponse('Error en la carga del archivo en Flask', status=500)

    template = loader.get_template('Index.html')
    return HttpResponse(template.render())