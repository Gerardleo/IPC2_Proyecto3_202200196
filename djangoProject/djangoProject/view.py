import requests
from django.http import HttpResponse
from django.template import loader
from requests import post,get
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime




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



@csrf_exempt
def cargar_archivo_mensajes(request):
    if request.method == 'POST':  # Verifica si la solicitud es de tipo POST
        archivo = request.FILES.get('archivo_mensajes')
        template = loader.get_template('Index.html')
        print("hola")
        if archivo:
            # Crear una solicitud POST al backend de Flask
            url_flask = ruta + '/grabarMensajes'
            files = {'archivo': archivo}
            response = post(url_flask, files=files)
            print(response)

            if response.status_code == 200:
                print("Archivo cargado correctamente")
                respuesta = 'Archivo cargado correctamente'
        else:
            print("Error al cargar el archivo")
            respuesta = 'Error al cargar el archivo'

    return HttpResponse(template.render({'respuesta':respuesta},request))

@csrf_exempt
def cargar_archivo_config(request):
    if request.method == 'POST':  # Verifica si la solicitud es de tipo POST
        archivo = request.FILES.get('archivo_config')
        template = loader.get_template('Index.html')
        if archivo:
            # Crear una solicitud POST al backend de Flask
            url_flask = ruta + '/grabarConfiguracion'
            files = {'archivo': archivo}
            response = post(url_flask, files=files)
            print(response)
            template = loader.get_template('Index.html')

            if response.status_code == 200:
                print("Archivo cargado correctamente")
                respuesta = 'Archivo cargado correctamente'
        else:
            print("Error al cargar el archivo")
            respuesta = 'Error al cargar el archivo'

    return HttpResponse(template.render({'respuesta':respuesta},request))

@csrf_exempt
def limpiar_datos(request):
    template = loader.get_template('Index.html')
    respuesta = ''
    if request.method == 'GET':
        url_flask = ruta + '/limpiarDatos'
        response = post(url_flask)
        print(response)

        if response.status_code == 200:
            print("Datos limpiados correctamente")
            respuesta = 'Datos limpiados correctamente'
        else:
            print("Error al limpiar datos")
            respuesta = 'Error al limpiar datos'

    return HttpResponse(template.render({'respuesta':respuesta},request))

def peticiones(request):
    template = loader.get_template('peticiones.html')
    return HttpResponse(template.render({'data_menciones': "1", 'respuesta': '', 'data_hashtags': "1"}, request))

@csrf_exempt
def buscarMenciones(request):
    template = loader.get_template('peticiones.html')
    respuesta = ''

    if request.method == 'GET':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            respuesta = 'Ambas fechas son requeridas para realizar la búsqueda.'
        else:
            # Realiza la búsqueda de menciones utilizando las fechas proporcionadas
            # Debes llamar a tu función de Flask para obtener los resultados en JSON

            # Aquí debes hacer la solicitud a tu backend de Flask y procesar la respuesta
            # Reemplaza este código con tu lógica para hacer la solicitud a Flask

            url_flask = ruta + '/obtenerMencionesPorRango'
            data = {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
            response = get(url_flask, data=data)

            if response.status_code == 200 or response.status_code == 404:
                # Aquí procesa la respuesta JSON que recibes de Flask
                # Puedes guardar los datos en una variable y pasarlos al template

                # Ejemplo hipotético
                menciones_data = response.json()
                print(menciones_data)

                return HttpResponse(template.render({'data_menciones': menciones_data, 'data_hashtags': '1', 'data_sentimientos': "1", 'respuesta': respuesta}, request))
            else:
                respuesta = 'Error al buscar menciones.'

    return HttpResponse(template.render({'respuesta': respuesta,"data_sentimientos": "1", 'data_menciones': "1", 'data_hashtags': "1"}, request))

@csrf_exempt
def buscarHastaghs(request):
    template = loader.get_template('peticiones.html')
    respuesta = ''

    if request.method == 'GET':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            respuesta = 'Ambas fechas son requeridas para realizar la búsqueda.'
        else:
            # Realiza la búsqueda de menciones utilizando las fechas proporcionadas
            # Debes llamar a tu función de Flask para obtener los resultados en JSON

            # Aquí debes hacer la solicitud a tu backend de Flask y procesar la respuesta
            # Reemplaza este código con tu lógica para hacer la solicitud a Flask

            url_flask = ruta + '/obtenerHashtagsPorRango'
            data = {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
            response = get(url_flask, data=data)

            if response.status_code == 200 or response.status_code == 404:
                # Aquí procesa la respuesta JSON que recibes de Flask
                # Puedes guardar los datos en una variable y pasarlos al template

                # Ejemplo hipotético
                hashtags_data = response.json()
                print(hashtags_data)

                return HttpResponse(template.render({'data_hashtags': hashtags_data, 'data_menciones': "1",'data_sentimientos': "1", 'respuesta':respuesta}, request))
            else:
                respuesta = 'Error al buscar hashtags.'

    return HttpResponse(template.render({'respuesta': respuesta, 'data_sentimientos': "1",'data_menciones': "1"}, request))

@csrf_exempt
def buscarSentimientos(request):
    template = loader.get_template('peticiones.html')
    respuesta = ''

    if request.method == 'GET':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            respuesta = 'Ambas fechas son requeridas para realizar la búsqueda.'
        else:
            # Realiza la búsqueda de menciones utilizando las fechas proporcionadas
            # Debes llamar a tu función de Flask para obtener los resultados en JSON

            # Aquí debes hacer la solicitud a tu backend de Flask y procesar la respuesta
            # Reemplaza este código con tu lógica para hacer la solicitud a Flask

            url_flask = ruta + '/consultarSentimientos'
            data = {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
            response = get(url_flask, data=data)

            if response.status_code == 200 or response.status_code == 404:
                # Aquí procesa la respuesta JSON que recibes de Flask
                # Puedes guardar los datos en una variable y pasarlos al template

                # Ejemplo hipotético
                sentimientos_data = response.json()
                print(sentimientos_data)

                return HttpResponse(template.render({'data_sentimientos': sentimientos_data, 'data_menciones': "1", 'data_hashtags': "1", 'respuesta':respuesta}, request))
            else:
                respuesta = 'Error al buscar sentimientos.'

    return HttpResponse(template.render({'respuesta': respuesta , 'data_menciones': "1", 'data_hashtags': "1"}, request))


@csrf_exempt
def guardarDatos(request):
    template = loader.get_template('Index.html')
    respuesta = ''
    if request.method == 'GET':
        url_flask = ruta + '/grabarDatos'
        response = post(url_flask)
        print(response)

        if response.status_code == 200:
            print("Datos guardados correctamente")
            respuesta = 'Datos guardados correctamente'
        else:
            print("Error al guardar datos")
            respuesta = 'Error al guardar datos'

    return HttpResponse(template.render({'respuesta':respuesta},request))
