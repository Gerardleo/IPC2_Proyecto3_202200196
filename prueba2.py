import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from xml.dom.minidom import Document, parseString
from flask import Flask, request, jsonify


app = Flask(__name__)



@app.route('/grabarMensajes', methods=['POST'])
def procesar_archivo_mensajes():
    global mensajes_recibidos, usuarios_mencionados, hashtags_incluidos, menciones_usuario, menciones_hashtag

    archivo = request.files.get('archivo')  # Usamos request.files.get para evitar errores si no se proporciona un archivo

    if archivo.filename == '':
        return jsonify({"error": "No se ha proporcionado ningún archivo"}), 400

    # Parsear el archivo de entrada de mensajes
    tree = ET.parse(archivo)
    root = tree.getroot()
    for mensaje in root.findall('MENSAJE'):
        fecha = mensaje.find('FECHA').text.strip().split(',')[1].strip()  # Extraer la fecha en el formato "dd/mm/yyyy"

        # Inicializar las menciones y hashtags para este mensaje
        menciones_mensaje = set()
        hashtags_mensaje = set()

        texto = mensaje.find('TEXTO').text.strip().lower()  # Convertir a minúsculas

        # Dividir el texto en palabras y contar usuarios y hashtags para este mensaje
        palabras = texto.split()
        for palabra in palabras:
            if palabra.startswith('@'):
                nombre_usuario = palabra[1:]
                menciones_mensaje.add(nombre_usuario)
                usuarios_mencionados.add(nombre_usuario)
                # Actualizar el contador de menciones de este usuario
                if nombre_usuario in menciones_usuario:
                    menciones_usuario[nombre_usuario] += 1
                else:
                    menciones_usuario[nombre_usuario] = 1
            elif palabra.startswith('#'):
                hashtag = palabra[1:]
                hashtags_mensaje.add(hashtag)
                hashtags_incluidos.add(hashtag)
                # Actualizar el contador de menciones de este hashtag
                if hashtag in menciones_hashtag:
                    menciones_hashtag[hashtag] += 1
                else:
                    menciones_hashtag[hashtag] = 1

        # Actualizar la información por fecha
        if fecha in mensajes_recibidos:
            mensajes_recibidos[fecha].append({
                'MSJ_RECIBIDOS': 1,
                'USR_MENCIONADOS': list(menciones_mensaje),
                'HASH_INCLUIDOS': list(hashtags_mensaje)
            })
        else:
            mensajes_recibidos[fecha] = [{
                'MSJ_RECIBIDOS': 1,
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
    global mensajes_recibidos
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
                ET.SubElement(tiempo, 'MSJ_RECIBIDOS').text = str(mensaje['MSJ_RECIBIDOS'])
                ET.SubElement(tiempo, 'USR_MENCIONADOS').text = str(len(mensaje['USR_MENCIONADOS']))
                ET.SubElement(tiempo, 'HASH_INCLUIDOS').text = str(len(mensaje['HASH_INCLUIDOS']))

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

    # Contar palabras en la lista de sentimientos positivos y sumar al contador global
    palabras_positivas += len(root.find('sentimientos_positivos').findall('palabra'))

    # Contar palabras en la lista de sentimientos negativos y sumar al contador global
    palabras_negativas += len(root.find('sentimientos_negativos').findall('palabra'))

    palabras_negativas_rechazadas += len(root.find('sentimientos_negativos').findall('palabra_rechazada'))

    palabras_positivas_rechazadas += len(root.find('sentimientos_positivos').findall('palabra_rechazada'))

    return json.dumps({
        "palabras_positivas": palabras_positivas,
        "palabras_negativas": palabras_negativas,
        "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
        "palabras_positivas_rechazadas": palabras_positivas_rechazadas
    }, indent=4)

@app.route('/generarSalidaConfig', methods=['GET'])
def generar_archivo_resumen_config():
    global palabras_positivas, palabras_negativas, palabras_negativas_rechazadas, palabras_positivas_rechazadas
    archivo_salida = "resumenConfig.xml"	

    # Crear el documento XML de salida
    doc = Document()
    config_recibida = doc.createElement('CONFIG_RECIBIDA')
    doc.appendChild(config_recibida)

    # Agregar el número de palabras positivas acumuladas
    palabras_positivas_element = doc.createElement('PALABRAS_POSITIVAS')
    palabras_positivas_element.appendChild(doc.createTextNode(str(palabras_positivas)))
    config_recibida.appendChild(palabras_positivas_element)

    # Agregar el número de palabras positivas rechazadas (en este ejemplo, establecido en 0)
    palabras_positivas_rechazadas_element = doc.createElement('PALABRAS_POSITIVAS_RECHAZADAS')
    palabras_positivas_rechazadas_element.appendChild(doc.createTextNode(str(palabras_positivas_rechazadas)))
    config_recibida.appendChild(palabras_positivas_rechazadas_element)

    # Agregar el número de palabras negativas acumuladas
    palabras_negativas_element = doc.createElement('PALABRAS_NEGATIVAS')
    palabras_negativas_element.appendChild(doc.createTextNode(str(palabras_negativas)))
    config_recibida.appendChild(palabras_negativas_element)

    # Agregar el número de palabras negativas rechazadas (en este ejemplo, establecido en 0)
    palabras_negativas_rechazadas_element = doc.createElement('PALABRAS_NEGATIVAS_RECHAZADAS')
    palabras_negativas_rechazadas_element.appendChild(doc.createTextNode(str(palabras_negativas_rechazadas)))
    config_recibida.appendChild(palabras_negativas_rechazadas_element)

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

    hashtags_contados = {}  # Diccionario para almacenar los hashtags y sus cantidades

    for mensajes in mensajes_recibidos.values():
        for mensaje in mensajes:
            for hashtag in mensaje['HASH_INCLUIDOS']:
                if hashtag in hashtags_contados:
                    hashtags_contados[hashtag] += 1
                else:
                    hashtags_contados[hashtag] = 1

    if not hashtags_contados:
        return "No se encontraron hashtags en los mensajes."
    else:
        return hashtags_contados

@app.route('/devolverMenciones', methods=['GET'])
def contar_menciones():
    global mensajes_recibidos
    menciones_contadas = {}  # Diccionario para almacenar las menciones y sus cantidades

    for mensajes in mensajes_recibidos.values():
        for mensaje in mensajes:
            for mencion in mensaje['USR_MENCIONADOS']:
                if mencion in menciones_contadas:
                    menciones_contadas[mencion] += 1
                else:
                    menciones_contadas[mencion] = 1

    if not menciones_contadas:
        return "No se encontraron menciones en los mensajes."
    else:
        return menciones_contadas

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
            "menciones_hashtag": menciones_hashtag
        }
        json.dump(data, json_file)
        
    return 'Datos guardados con éxito'




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

    app.run(debug=True, port=5000)





