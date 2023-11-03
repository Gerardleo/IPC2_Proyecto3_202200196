import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from xml.dom.minidom import Document, parseString
from flask import Flask, request, jsonify
from unidecode import unidecode
from datetime import datetime
from collections import defaultdict
from flask import send_file
import re



app = Flask(__name__)


@app.route('/grabarMensajes', methods=['POST'])
def procesar_archivo_mensajes():
    archivo = request.files.get('archivo')

    if archivo.filename == '':
        return jsonify({"error": "No se ha proporcionado ningún archivo"}), 400

    # Parsear el archivo de entrada de mensajes
    tree = ET.parse(archivo)
    root = tree.getroot()

    fecha_hora_regex = r'(\d{2}/\d{2}/\d{4})'  # Patrón de fecha
    lugar_regex = r'[^,\d\n]*(?=(?:, \d{2}/\d{2}/\d{4} \d{1,2}:\d{2} hrs\.|$))'  # Patrón de lugar
    hora_regex = r'(\d{1,2}:\d{2} hrs\.)' # Patrón de hora

    for mensaje in root.findall('MENSAJE'):
        fecha_hora = mensaje.find('FECHA').text.strip()

        fecha_match = re.search(fecha_hora_regex, fecha_hora)
        lugar_match = re.search(lugar_regex, fecha_hora)
        hora_match = re.search(hora_regex, fecha_hora)

        if fecha_match:
            fecha_str = fecha_match.group(0)
            fecha_obj = datetime.strptime(fecha_str, '%d/%m/%Y')
        else:
            # Manejar el caso en el que la fecha no se encuentre
            fecha_obj = None

        if lugar_match:
            lugar = lugar_match.group(0).strip()
        else:
            lugar = None

        if hora_match:
            hora_str = hora_match.group(0)
            hora = datetime.strptime(hora_str, '%H:%M hrs.').time()
        else:
            hora = None

        if fecha_obj:
            fecha = fecha_obj.strftime('%d/%m/%Y')  # Convertir la fecha a una cadena en el formato deseado
        else:
            fecha = None

            # Parsear la fecha a un objeto datetime
        
        # Inicializar las menciones y hashtags para este mensaje
        menciones_mensaje = set()
        hashtags_mensaje = set()

        texto = mensaje.find('TEXTO').text.strip()
        # Normalizar el texto para ignorar mayúsculas y minúsculas y tildes
        texto = unidecode(texto).lower()

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
        if fecha:
            if fecha in mensajes_recibidos:
                mensajes_recibidos[fecha].append({
                    'LUGAR': lugar,
                    'HORA': hora.strftime('%H:%M:%S') if hora else None,  # Convertir la hora a una cadena en formato 'HH:MM:SS'
                    'MENSAJE': mensaje.find('TEXTO').text.strip(),
                    'USR_MENCIONADOS': list(menciones_mensaje),
                    'HASH_INCLUIDOS': list(hashtags_mensaje)
                })
            else:
                mensajes_recibidos[fecha] = [{
                    'LUGAR': lugar,
                    'HORA': hora.strftime('%H:%M:%S') if hora else None,  # Convertir la hora a una cadena en formato 'HH:MM:SS'
                    'MENSAJE': mensaje.find('TEXTO').text.strip(),
                    'USR_MENCIONADOS': list(menciones_mensaje),
                    'HASH_INCLUIDOS': list(hashtags_mensaje)
                }]
    generar_archivo_salida()
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

                if mensaje['HORA'] is not None:
                    # Manejar la hora, asegurándose de que esté en el formato "hh:mm"
                    hora = mensaje['HORA'].split(' ')[0]
                else:
                    # Si la hora es None, asignar un valor predeterminado o manejarlo como desees
                    hora = "00:00"

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
def contar_palabras_en_apartados():
    archivo = request.files.get('archivo')
    
    if archivo.filename == '':
        return jsonify({"error": "No se ha proporcionado ningún archivo"}), 400

    tree = ET.parse(archivo)
    root = tree.getroot()

    palabras_positivas = root.find('sentimientos_positivos').findall('palabra')
    palabras_negativas = root.find('sentimientos_negativos').findall('palabra')
    
    # Buscar los sentimientos neutros si existen
    sentimientos_neutros = root.find('sentimientos_neutros')
    if sentimientos_neutros is not None:
        palabras_neutras = sentimientos_neutros.findall('palabra')
    else:
        palabras_neutras = []

    palabras_positivas_rechazadas = root.find('sentimientos_positivos').findall('palabra_rechazada')
    palabras_negativas_rechazadas = root.find('sentimientos_negativos').findall('palabra_rechazada')

    conteo_palabras = {
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "palabras_positivas": len(palabras_positivas),
        "palabras_negativas": len(palabras_negativas),
        "palabras_neutras": len(palabras_neutras),  
        "palabras_positivas_rechazadas": len(palabras_positivas_rechazadas),
        "palabras_negativas_rechazadas": len(palabras_negativas_rechazadas)
    }
    historial_configuraciones.append(conteo_palabras)
    generar_archivo_resumen_config()
    return json.dumps({
        "palabras_positivas": len(palabras_positivas),
        "palabras_negativas": len(palabras_negativas),
        "palabras_neutras": len(palabras_neutras),  
        "palabras_positivas_rechazadas": len(palabras_positivas_rechazadas),
        "palabras_negativas_rechazadas": len(palabras_negativas_rechazadas),
    }, indent=4)


@app.route('/obtenerHistorialConfiguraciones', methods=['GET'])
def obtener_historial_configuraciones():
    return jsonify({"historial_configuraciones": historial_configuraciones})


@app.route('/generarSalidaConfig', methods=['GET'])
def generar_archivo_resumen_config():
    global palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas, historial_configuraciones,palabras_neutras

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

        palabras_neutras_element = doc.createElement('PALABRAS_NEUTRAS')
        palabras_neutras_element.appendChild(doc.createTextNode(str(configuracion['palabras_neutras'])))
        configuracion_element.appendChild(palabras_neutras_element)  # Adjuntado dentro de configuracion_element

        # Agregar los demás datos de configuración (palabras positivas, negativas, rechazadas, etc.)

    # Generar el archivo de salida en el formato deseado
    with open(archivo_salida, 'w', encoding='utf-8') as output_file:
        output_file.write(doc.toprettyxml(indent=" "))
    
    return "Archivo de salida generado con éxito"

@app.route('/limpiarDatos', methods=['POST'])
def reiniciar_datos_globales():
    global mensajes_recibidos, usuarios_mencionados, hashtags_incluidos, palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas, historial_configuraciones
    mensajes_recibidos = {}
    usuarios_mencionados = set()
    hashtags_incluidos = set()
    palabras_positivas = 0
    palabras_negativas = 0
    palabras_neutras = 0
    palabras_negativas_rechazadas = 0
    palabras_positivas_rechazadas = 0
    historial_configuraciones = []

    return json.dumps({
        "mensajes_recibidos": mensajes_recibidos,
        "usuarios_mencionados": list(usuarios_mencionados),
        "hashtags_incluidos": list(hashtags_incluidos),
        "palabras_positivas": palabras_positivas,
        "palabras_negativas": palabras_negativas,
        "palabras_neutras": palabras_neutras,
        "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
        "palabras_positivas_rechazadas": palabras_positivas_rechazadas,
        "configuracion_por_fecha": historial_configuraciones
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



@app.route('/obtenerHashtagsPorRango', methods=['GET'])
def contar_hashtags_por_rango():
    codigoRespuesta = 1
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')
    
    if fecha_inicio is None or fecha_fin is None:
        return jsonify({"error": "Las fechas de inicio y fin son requeridas"}), 400

    hashtags_por_fecha = defaultdict(lambda: defaultdict(int))  # Diccionario para contar hashtags por fecha

    # Iterar a través de las fechas dentro del rango
    for fecha in mensajes_recibidos:
        if fecha_inicio <= fecha <= fecha_fin:
            for mensaje in mensajes_recibidos[fecha]:
                hashtags = mensaje['HASH_INCLUIDOS']
                for hashtag in hashtags:
                    hashtags_por_fecha[fecha][hashtag] += 1

    if not hashtags_por_fecha:
        codigoRespuesta = 0
        return jsonify({"codigo": codigoRespuesta, "mensaje": "No se encontraron hashtags en el rango de fechas proporcionado."}), 404

    # Organizar los hashtags por fecha
    resultado = {
        "codigo": codigoRespuesta,
        "hashtags_por_fecha": dict(hashtags_por_fecha),
        "hashtags_totales": defaultdict(int)
    }

    # Calcular el contador total
    for fecha, hashtags in hashtags_por_fecha.items():
        for hashtag, conteo in hashtags.items():
            resultado["hashtags_totales"][hashtag] += conteo

    return jsonify(resultado)


@app.route('/obtenerMencionesPorRango', methods=['GET'])
def contar_menciones_por_rango():
    codigoRespuesta = 1
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio is None or fecha_fin is None:
        return jsonify({"Las fechas de inicio y fin son requeridas"}), 400

    menciones_por_fecha = defaultdict(lambda: defaultdict(int))  # Diccionario para contar menciones por fecha

    # Iterar a través de las fechas dentro del rango
    for fecha in mensajes_recibidos:
        if fecha_inicio <= fecha <= fecha_fin:
            for mensaje in mensajes_recibidos[fecha]:
                menciones = mensaje['USR_MENCIONADOS']
                for mencion in menciones:
                    menciones_por_fecha[fecha][mencion] += 1

    if not menciones_por_fecha:
        codigoRespuesta = 0
        return jsonify({"codigo": codigoRespuesta, "mensaje": "No se encontraron menciones en el rango de fechas proporcionado."}), 404

    # Organizar las menciones por fecha
    resultado = {
        "codigo": codigoRespuesta,
        "menciones_por_fecha": dict(menciones_por_fecha),
        "menciones_usuario_totales": defaultdict(int)
    }

    # Calcular el contador total
    for fecha, menciones in menciones_por_fecha.items():
        for mencion, conteo in menciones.items():
            resultado["menciones_usuario_totales"][mencion] += conteo

    return jsonify(resultado)

@app.route('/consultarSentimientos', methods=['GET'])
def consultar_sentimientos():
    codigoRespuesta = 1
    fecha_inicio_str = request.form.get('fecha_inicio')
    fecha_fin_str = request.form.get('fecha_fin')

    if not fecha_inicio_str or not fecha_fin_str:
        # Si falta alguno de los parámetros, devuelve un mensaje de error
        return jsonify({"Mensaje": "Los parámetros 'fecha_inicio' y 'fecha_fin' son obligatorios."}), 400

    # Convierte las fechas de cadena a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%d-%m-%Y")
    fecha_fin = datetime.strptime(fecha_fin_str, "%d-%m-%Y")

    # Inicializar un diccionario para almacenar las menciones de palabras por fecha y hora, incluyendo segundos
    menciones_por_fecha_hora = defaultdict(dict)

    # Calcular el total de palabras en todas las configuraciones dentro del rango de fechas
    total_palabras_positivas = 0
    total_palabras_negativas = 0
    total_palabras_positivas_rechazadas = 0
    total_palabras_negativas_rechazadas = 0
    total_palabras_neutras = 0

    for configuracion in historial_configuraciones:
        fecha_configuracion = datetime.strptime(configuracion["fecha"], "%d/%m/%Y")
        hora_configuracion = configuracion.get("hora", "")
        
        if fecha_inicio <= fecha_configuracion <= fecha_fin:
            palabras_positivas = configuracion.get("palabras_positivas", 0)
            palabras_negativas = configuracion.get("palabras_negativas", 0)
            palabras_neutras = configuracion.get("palabras_neutras", 0)
            palabras_positivas_rechazadas = configuracion.get("palabras_positivas_rechazadas", 0)
            palabras_negativas_rechazadas = configuracion.get("palabras_negativas_rechazadas", 0)

            # Actualizar los totales de palabras
            total_palabras_positivas += palabras_positivas
            total_palabras_negativas += palabras_negativas
            total_palabras_neutras += palabras_neutras
            total_palabras_positivas_rechazadas += palabras_positivas_rechazadas
            total_palabras_negativas_rechazadas += palabras_negativas_rechazadas

            # Construir la clave para la fecha y hora, incluyendo segundos
            fecha_hora_str = f"{fecha_configuracion.strftime('%d/%m/%Y')} {hora_configuracion}"

            # Actualizar las menciones de palabras por fecha y hora
            menciones_por_fecha_hora[fecha_hora_str]["palabras_positivas"] = palabras_positivas
            menciones_por_fecha_hora[fecha_hora_str]["palabras_negativas"] = palabras_negativas
            menciones_por_fecha_hora[fecha_hora_str]["palabras_positivas_rechazadas"] = palabras_positivas_rechazadas
            menciones_por_fecha_hora[fecha_hora_str]["palabras_negativas_rechazadas"] = palabras_negativas_rechazadas
            menciones_por_fecha_hora[fecha_hora_str]["palabras_neutras"] = palabras_neutras
            
    if not menciones_por_fecha_hora:
        codigoRespuesta = 0
        return jsonify({"codigo": codigoRespuesta, "mensaje": "No se encontraron sentimientos en el rango de fechas proporcionado."}), 404

    return jsonify({
        "codigo": codigoRespuesta,
        "menciones_por_fecha_hora": menciones_por_fecha_hora,
        "total_palabras": {
            "positivas": total_palabras_positivas,
            "negativas": total_palabras_negativas,
            "neutras": total_palabras_neutras,
            "positivas_rechazadas": total_palabras_positivas_rechazadas,
            "negativas_rechazadas": total_palabras_negativas_rechazadas
        }
    })

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
            palabras_neutras = data.get("palabras_neutras", 0)  
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
        palabras_neutras = 0
        palabras_negativas_rechazadas = 0
        palabras_positivas_rechazadas = 0
        historial_configuraciones = []

    app.run(debug=True, port=5000)





