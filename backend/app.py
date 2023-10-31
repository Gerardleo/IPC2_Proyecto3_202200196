import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from xml.dom.minidom import Document, parseString
from flask import Flask, request, jsonify
from unidecode import unidecode
from datetime import datetime



app = Flask(__name__)


@app.route('/grabarMensajes', methods=['POST'])
def procesar_archivo_mensajes():
    archivo = request.files.get('archivo')

    if archivo.filename == '':
        return jsonify({"error": "No se ha proporcionado ningún archivo"}), 400

    # Parsear el archivo de entrada de mensajes
    tree = ET.parse(archivo)
    root = tree.getroot()

    for mensaje in root.findall('MENSAJE'):
        fecha_hora = mensaje.find('FECHA').text.strip()
        lugar, fecha_hora = fecha_hora.split(', ')
        fecha_hora = fecha_hora.strip().split(' ')
        fecha = fecha_hora[0]
        hora = fecha_hora[1]

        # Parsear la fecha a un objeto datetime
        fecha_obj = datetime.strptime(fecha, '%d/%m/%Y')
        
        # Inicializar las menciones y hashtags para este mensaje
        menciones_mensaje = set()
        hashtags_mensaje = set()

        texto = mensaje.find('TEXTO').text.strip().lower()

        # Dividir el texto en palabras y contar usuarios y hashtags para este mensaje
        palabras = texto.split()
        for palabra in palabras:
            if palabra.startswith('@'):
                nombre_usuario = palabra[1:]
                menciones_mensaje.add(nombre_usuario)
                usuarios_mencionados.add(nombre_usuario)
                menciones_usuario[nombre_usuario] = menciones_usuario.get(nombre_usuario, 0) + 1
            elif palabra.startswith('#'):
                hashtag = palabra[1:]
                hashtag_sin_tildes = unidecode(hashtag)
                hashtags_mensaje.add(hashtag_sin_tildes)
                hashtags_incluidos.add(hashtag_sin_tildes)
                menciones_hashtag[hashtag_sin_tildes] = menciones_hashtag.get(hashtag_sin_tildes, 0) + 1

        # Actualizar la información por fecha
        if fecha in mensajes_recibidos:
            mensajes_recibidos[fecha].append({
                'LUGAR': lugar,
                'HORA': hora,
                'MENSAJE': mensaje.find('TEXTO').text.strip(),
                'USR_MENCIONADOS': list(menciones_mensaje),
                'HASH_INCLUIDOS': list(hashtags_mensaje)
            })
        else:
            mensajes_recibidos[fecha] = [{
                'LUGAR': lugar,
                'HORA': hora,
                'MENSAJE': mensaje.find('TEXTO').text.strip(),
                'USR_MENCIONADOS': list(menciones_mensaje),
                'HASH_INCLUIDOS': list(hashtags_mensaje)
            }]

    return json.dumps({
        "mensajes_recibidos": mensajes_recibidos,
        "usuarios_mencionados": list(usuarios_mencionados),
        "hashtags_incluidos": list(hashtags_incluidos),
        "menciones_usuario": menciones_usuario,
        "menciones_hashtag": menciones_hashtag
    }, indent=4)


@app.route('/generarSalida', methods=['GET'])
def generar_archivo_salida():
    archivo_salida = "resumenMensajes.xml"

    # Crear el archivo de salida "resumenMensajes.xml" con el formato deseado
    resumen_mensajes = ET.Element('MENSAJES_RECIBIDOS')

    if not mensajes_recibidos:
        # Si no hay mensajes, añadir un elemento "TIEMPO" vacío
        tiempo = ET.SubElement(resumen_mensajes, 'TIEMPO')
        ET.SubElement(tiempo, 'FECHA')
        ET.SubElement(tiempo, 'MSJ_RECIBIDOS').text = '0'
        ET.SubElement(tiempo, 'USR_MENCIONADOS').text = '0'
        ET.SubElement(tiempo, 'HASH_INCLUIDOS').text = '0'
    else:
        # Si hay mensajes, generar elementos "TIEMPO" según los mensajes
        for fecha, mensajes in mensajes_recibidos.items():
            for mensaje in mensajes:
                tiempo = ET.SubElement(resumen_mensajes, 'TIEMPO')
                ET.SubElement(tiempo, 'FECHA').text = fecha

                # Manejar la hora, asegurándose de que esté en el formato "hh:mm"
                hora = mensaje['HORA'].split(' ')[0]
                ET.SubElement(tiempo, 'HORA').text = hora

                # Contar usuarios mencionados y hashtags incluidos
                usuarios_mencionados = mensaje['USR_MENCIONADOS']
                hashtags_incluidos = mensaje['HASH_INCLUIDOS']
                ET.SubElement(tiempo, 'MSJ_RECIBIDOS').text = str(1)  # Siempre 1 mensaje
                ET.SubElement(tiempo, 'USR_MENCIONADOS').text = str(len(usuarios_mencionados))
                ET.SubElement(tiempo, 'HASH_INCLUIDOS').text = str(len(hashtags_incluidos))

    # Generar el archivo de salida en formato XML
    rough_string = ET.tostring(resumen_mensajes, 'utf-8')
    reparsed = parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent=" ")

    # Guardar el archivo de salida
    with open(archivo_salida, 'w', encoding='utf-8') as output_file:
        output_file.write(pretty_xml)

    return "Archivo de salida generado con éxito"

@app.route('/grabarConfiguracion', methods=['POST'])
def leer_archivo_config():
    global palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas

    archivo = request.files.get('archivo')  # Usamos request.files.get para evitar errores si no se proporciona un archivo

    if archivo.filename == '':
        return jsonify({"error": "No se ha proporcionado ningún archivo"}), 400

    # Parsear el archivo de configuración del diccionario de sentimientos
    tree = ET.parse(archivo)
    root = tree.getroot()

    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")

    # Contar palabras en la lista de sentimientos positivos y sumar al contador global
    palabras_positivas = len(root.find('sentimientos_positivos').findall('palabra'))

    # Contar palabras en la lista de sentimientos negativos y sumar al contador global
    palabras_negativas = len(root.find('sentimientos_negativos').findall('palabra'))

    palabras_negativas_rechazadas = len(root.find('sentimientos_negativos').findall('palabra_rechazada'))

    palabras_positivas_rechazadas = len(root.find('sentimientos_positivos').findall('palabra_rechazada'))

    # Guardar la configuración actual en el historial de configuraciones
    configuracion_actual = {
        "fecha": str(fecha_actual),
        "hora": str(hora_actual),
        "palabras_positivas": palabras_positivas,
        "palabras_negativas": palabras_negativas,
        "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
        "palabras_positivas_rechazadas": palabras_positivas_rechazadas
    }
    historial_configuraciones.append(configuracion_actual)

    return json.dumps(configuracion_actual, indent=4)

@app.route('/obtenerHistorialConfiguraciones', methods=['GET'])
def obtener_historial_configuraciones():
    return jsonify({"historial_configuraciones": historial_configuraciones})


@app.route('/generarSalidaConfig', methods=['GET'])
def generar_archivo_resumen_config():
    global palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas, historial_configuraciones

    archivo_salida = "resumenConfig.xml"

    # Crear el documento XML de salida
    doc = Document()
    config_recibida = doc.createElement('CONFIG_RECIBIDA')
    doc.appendChild(config_recibida)

    for configuracion in historial_configuraciones:
        configuracion_element = doc.createElement('CONFIGURACION')
        config_recibida.appendChild(configuracion_element)

        fecha_element = doc.createElement('FECHA')
        fecha_element.appendChild(doc.createTextNode(configuracion['fecha']))
        configuracion_element.appendChild(fecha_element)  # Adjuntado dentro de configuracion_element

        hora_element = doc.createElement('HORA')
        hora_element.appendChild(doc.createTextNode(configuracion['hora']))
        configuracion_element.appendChild(hora_element)  # Adjuntado dentro de configuracion_element

        palabras_positivas_element = doc.createElement('PALABRAS_POSITIVAS')
        palabras_positivas_element.appendChild(doc.createTextNode(str(configuracion['palabras_positivas'])))
        configuracion_element.appendChild(palabras_positivas_element)  # Adjuntado dentro de configuracion_element

        # Agregar el número de palabras positivas rechazadas
        palabras_positivas_rechazadas_element = doc.createElement('PALABRAS_POSITIVAS_RECHAZADAS')
        palabras_positivas_rechazadas_element.appendChild(doc.createTextNode(str(configuracion['palabras_positivas_rechazadas'])))
        configuracion_element.appendChild(palabras_positivas_rechazadas_element)  # Adjuntado dentro de configuracion_element

        # Agregar el número de palabras negativas acumuladas
        palabras_negativas_element = doc.createElement('PALABRAS_NEGATIVAS')
        palabras_negativas_element.appendChild(doc.createTextNode(str(configuracion['palabras_negativas'])))
        configuracion_element.appendChild(palabras_negativas_element)  # Adjuntado dentro de configuracion_element

        # Agregar el número de palabras negativas rechazadas
        palabras_negativas_rechazadas_element = doc.createElement('PALABRAS_NEGATIVAS_RECHAZADAS')
        palabras_negativas_rechazadas_element.appendChild(doc.createTextNode(str(configuracion['palabras_negativas_rechazadas'])))
        configuracion_element.appendChild(palabras_negativas_rechazadas_element)  # Adjuntado dentro de configuracion_element

        # Agregar los demás datos de configuración (palabras positivas, negativas, rechazadas, etc.)

    # Generar el archivo de salida en el formato deseado
    with open(archivo_salida, 'w', encoding='utf-8') as output_file:
        output_file.write(doc.toprettyxml(indent=" "))
    
    return "Archivo de salida generado con éxito"

@app.route('/limpiarDatos', methods=['POST'])
def reiniciar_datos_globales():
    global mensajes_recibidos, usuarios_mencionados, hashtags_incluidos, palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas
    mensajes_recibidos = {}
    usuarios_mencionados = set()
    hashtags_incluidos = set()
    palabras_positivas = 0
    palabras_negativas = 0
    palabras_negativas_rechazadas = 0
    palabras_positivas_rechazadas = 0

    return json.dumps({
        "mensajes_recibidos": mensajes_recibidos,
        "usuarios_mencionados": list(usuarios_mencionados),
        "hashtags_incluidos": list(hashtags_incluidos),
        "palabras_positivas": palabras_positivas,
        "palabras_negativas": palabras_negativas,
        "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
        "palabras_positivas_rechazadas": palabras_positivas_rechazadas
    }, indent=4)

@app.route('/devolverHashtags', methods=['GET'])
def contar_hashtags():
    global mensajes_recibidos
    codigoRespuesta = 1

    hashtags_contados = {}  # Diccionario para almacenar los hashtags y sus cantidades

    for mensajes in mensajes_recibidos.values():
        for mensaje in mensajes:
            for hashtag in mensaje['HASH_INCLUIDOS']:
                if hashtag in hashtags_contados:
                    hashtags_contados[hashtag] += 1
                else:
                    hashtags_contados[hashtag] = 1

    if not hashtags_contados:
        codigoRespuesta = 0
        return jsonify({"codigo":codigoRespuesta,"mensaje":"No se encontraron hashtags en los mensajes."}), 404
    else:
        return jsonify({"codigo":codigoRespuesta,"hashtags_contados": hashtags_contados})

@app.route('/devolverMenciones', methods=['GET'])
def contar_menciones():
    global mensajes_recibidos
    codigoRespuesta = 1
    menciones_contadas = {}  # Diccionario para almacenar las menciones y sus cantidades

    for mensajes in mensajes_recibidos.values():
        for mensaje in mensajes:
            for mencion in mensaje['USR_MENCIONADOS']:
                if mencion in menciones_contadas:
                    menciones_contadas[mencion] += 1
                else:
                    menciones_contadas[mencion] = 1

    if not menciones_contadas:
        codigoRespuesta = 0
        return jsonify({"codigo":codigoRespuesta,"mensaje":"No se encontraron menciones en los mensajes."}), 404
    else:
        return jsonify({"codigo":codigoRespuesta,"menciones_usuario": menciones_contadas})

@app.route('/grabarDatos', methods=['POST'])
def grabarDatos():
    # Tu código para procesar los mensajes

    # Guardar los datos en un archivo JSON
    with open('datos.json', 'w') as json_file:
        data = {
            "mensajes_recibidos": mensajes_recibidos,
            "usuarios_mencionados": list(usuarios_mencionados),
            "hashtags_incluidos": list(hashtags_incluidos),
            "menciones_usuario": menciones_usuario,
            "menciones_hashtag": menciones_hashtag,
            "palabras_positivas": palabras_positivas,
            "palabras_negativas": palabras_negativas,
            "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
            "palabras_positivas_rechazadas": palabras_positivas_rechazadas,
            "configuracion_por_fecha": historial_configuraciones
        }
        json.dump(data, json_file)
        
    return 'Datos guardados con éxito'


@app.route('/obtenerHastagPorRango', methods=['GET'])
def contar_hashtags_por_rango():
    codigoRespuesta = 1
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')
    
    if fecha_inicio is None or fecha_fin is None:
        return jsonify({"error": "Las fechas de inicio y fin son requeridas"}), 400

    hashtags_contados = {}  # Diccionario para contar hashtags

    # Iterar a través de las fechas dentro del rango
    for fecha in mensajes_recibidos:
        if fecha_inicio <= fecha <= fecha_fin:
            for mensaje in mensajes_recibidos[fecha]:
                hashtags = mensaje['HASH_INCLUIDOS']
                for hashtag in hashtags:
                    if hashtag in hashtags_contados:
                        hashtags_contados[hashtag] += 1
                    else:
                        hashtags_contados[hashtag] = 1

    if not hashtags_contados:
        codigoRespuesta = 0
        return jsonify({"codigo":codigoRespuesta,"mensaje":"No se encontraron hashtags en el rango de fechas proporcionado."}), 404

    return jsonify({"codigo":codigoRespuesta,"hashtags_contados": hashtags_contados})

@app.route('/obtenerMencionesPorRango', methods=['GET'])
def contar_menciones_por_rango():
    codigoRespuesta = 1
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio is None or fecha_fin is None:
        return jsonify({"Las fechas de inicio y fin son requeridas"}), 400

    menciones_contadas = {}  # Diccionario para contar menciones

    # Iterar a través de las fechas dentro del rango
    for fecha in mensajes_recibidos:
        if fecha_inicio <= fecha <= fecha_fin:
            for mensaje in mensajes_recibidos[fecha]:
                menciones = mensaje['USR_MENCIONADOS']
                for mencion in menciones:
                    if mencion in menciones_contadas:
                        menciones_contadas[mencion] += 1
                    else:
                        menciones_contadas[mencion] = 1
    if not menciones_contadas:
        codigoRespuesta = 0
        return jsonify({"codigo":codigoRespuesta,"mensaje":"No se encontraron menciones en el rango de fechas proporcionado."}), 404

    return jsonify({"codigo":codigoRespuesta,"menciones_usuario": menciones_contadas})


@app.route('/consultarSentimientos', methods=['GET'])
def consultar_sentimientos():
    codigoRespuesta = 1
    fecha_inicio_str = request.form.get('fecha_inicio')
    fecha_fin_str = request.form.get('fecha_fin')

    if not fecha_inicio_str or not fecha_fin_str:
        # Si falta alguno de los parámetros, devuelve un mensaje de error
        return jsonify({"Mensaje": "Los parámetros 'fecha_inicio' y 'fecha_fin' son obligatorios."}), 400

    # Convierte las fechas de cadena a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%d/%m/%Y")
    fecha_fin = datetime.strptime(fecha_fin_str, "%d/%m/%Y")

    # Realiza la búsqueda de configuraciones en el rango de fechas
    configuraciones_en_rango = []
    for configuracion in historial_configuraciones:
        fecha_configuracion = datetime.strptime(configuracion["fecha"], "%d/%m/%Y")
        if fecha_inicio <= fecha_configuracion <= fecha_fin:
            configuraciones_en_rango.append(configuracion)

    if configuraciones_en_rango == []:
        codigoRespuesta = 0
        return jsonify({"codigo":codigoRespuesta,"mensaje":"No se encontraron configuraciones en el rango de fechas proporcionado."}), 404

    return jsonify({"codigo":codigoRespuesta,"configuraciones_en_rango": configuraciones_en_rango})



if __name__ == "__main__":
    try:
        with open('datos.json', 'r') as json_file:
            data = json.load(json_file)
            mensajes_recibidos = data.get("mensajes_recibidos", {})
            usuarios_mencionados = set(data.get("usuarios_mencionados", []))
            hashtags_incluidos = set(data.get("hashtags_incluidos", []))
            menciones_usuario = data.get("menciones_usuario", {})
            menciones_hashtag = data.get("menciones_hashtag", {})
            palabras_positivas = data.get("palabras_positivas", 0)
            palabras_negativas = data.get("palabras_negativas", 0)
            palabras_negativas_rechazadas = data.get("palabras_negativas_rechazadas", 0) 
            palabras_positivas_rechazadas = data.get("palabras_positivas_rechazadas", 0)
            historial_configuraciones = data.get("configuracion_por_fecha", [])

    except FileNotFoundError:
        mensajes_recibidos = {}
        usuarios_mencionados = set()
        hashtags_incluidos = set()
        menciones_usuario = {}
        menciones_hashtag = {}
        palabras_positivas = 0
        palabras_negativas = 0
        palabras_negativas_rechazadas = 0
        palabras_positivas_rechazadas = 0
        historial_configuraciones = []

    app.run(debug=True, port=5000)





