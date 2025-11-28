from flask import Flask, render_template, request, jsonify,send_from_directory
import json
import os
import re

app = Flask(__name__)

# Orden correcto de los libros de la Biblia Reina Valera 1960
ORDEN_LIBROS = {
    "Antiguo Testamento": [
        "Génesis", "Éxodo", "Levítico", "Números", "Deuteronomio", "Josué", "Jueces", "Rut", 
        "1 Samuel", "2 Samuel", "1 Reyes", "2 Reyes", "1 Crónicas", "2 Crónicas", "Esdras", "Nehemías", 
        "Ester", "Job", "Salmos", "Proverbios", "Eclesiastés", "Cantares", "Isaías", "Jeremías", 
        "Lamentaciones", "Ezequiel", "Daniel", "Oseas", "Joel", "Amós", "Abdías", "Jonás", 
        "Miqueas", "Nahum", "Habacuc", "Sofonías", "Hageo", "Zacarías", "Malaquías"
    ],
    "Nuevo Testamento": [
        "Mateo", "Marcos", "Lucas", "Juan", "Hechos", "Romanos", "1 Corintios", "2 Corintios", 
        "Gálatas", "Efesios", "Filipenses", "Colosenses", "1 Tesalonicenses", "2 Tesalonicenses", 
        "1 Timoteo", "2 Timoteo", "Tito", "Filemón", "Hebreos", "Santiago", "1 Pedro", "2 Pedro", 
        "1 Juan", "2 Juan", "3 Juan", "Judas", "Apocalipsis"
    ]
}

# Lista plana de todos los libros para búsqueda
TODOS_LIBROS = ORDEN_LIBROS["Antiguo Testamento"] + ORDEN_LIBROS["Nuevo Testamento"]

# Mapeo de nombres alternativos para coincidencias flexibles
MAPEO_LIBROS = {
    # Antiguo Testamento
    "genesis": "Génesis",
    "exodo": "Éxodo", 
    "levitico": "Levítico",
    "numeros": "Números",
    "deuteronomio": "Deuteronomio",
    "josue": "Josué",
    "jueces": "Jueces",
    "rut": "Rut",
    "1 samuel": "1 Samuel",
    "2 samuel": "2 Samuel", 
    "1 reyes": "1 Reyes",
    "2 reyes": "2 Reyes",
    "1 cronicas": "1 Crónicas",
    "2 cronicas": "2 Crónicas",
    "esdras": "Esdras",
    "nehemias": "Nehemías",
    "ester": "Ester",
    "job": "Job",
    "salmos": "Salmos",
    "proverbios": "Proverbios",
    "eclesiastes": "Eclesiastés",
    "cantares": "Cantares",
    "isaias": "Isaías",
    "jeremias": "Jeremías",
    "lamentaciones": "Lamentaciones",
    "ezequiel": "Ezequiel",
    "daniel": "Daniel",
    "oseas": "Oseas",
    "joel": "Joel",
    "amos": "Amós",
    "abdias": "Abdías",
    "jonas": "Jonás",
    "miqueas": "Miqueas",
    "nahum": "Nahum",
    "habacuc": "Habacuc",
    "sofonias": "Sofonías",
    "hageo": "Hageo",
    "zacarias": "Zacarías",
    "malaquias": "Malaquías",
    
    # Nuevo Testamento
    "mateo": "Mateo",
    "marcos": "Marcos", 
    "lucas": "Lucas",
    "juan": "Juan",
    "hechos": "Hechos",
    "romanos": "Romanos",
    "1 corintios": "1 Corintios",
    "2 corintios": "2 Corintios",
    "galatas": "Gálatas",
    "efesios": "Efesios",
    "filipenses": "Filipenses",
    "colosenses": "Colosenses",
    "1 tesalonicenses": "1 Tesalonicenses",
    "2 tesalonicenses": "2 Tesalonicenses",
    "1 timoteo": "1 Timoteo",
    "2 timoteo": "2 Timoteo",
    "tito": "Tito",
    "filemon": "Filemón",
    "hebreos": "Hebreos",
    "santiago": "Santiago",
    "1 pedro": "1 Pedro",
    "2 pedro": "2 Pedro",
    "1 juan": "1 Juan",
    "2 juan": "2 Juan",
    "3 juan": "3 Juan",
    "judas": "Judas",
    "apocalipsis": "Apocalipsis",
    
    # Nombres con prefijos comunes
    "s. juan": "Juan",
    "s.juan": "Juan",
    "san juan": "Juan",
    "s. mateo": "Mateo", 
    "s.mateo": "Mateo",
    "san mateo": "Mateo",
    "s. marcos": "Marcos",
    "s.marcos": "Marcos", 
    "san marcos": "Marcos",
    "s. lucas": "Lucas",
    "s.lucas": "Lucas",
    "san lucas": "Lucas",
    "s. pedro": "1 Pedro",
    "s.pedro": "1 Pedro",
    "san pedro": "1 Pedro",
    "s. pablo": "Romanos",
    "s.pablo": "Romanos",
    "san pablo": "Romanos",
    "salmo": "Salmos"
}

def normalizar_nombre_libro(nombre):
    """Normaliza el nombre del libro para coincidencias consistentes"""
    if not nombre:
        return ""
    
    nombre = nombre.strip()
    
    # Limpiar prefijos comunes (S., San, etc.)
    nombre_limpio = re.sub(r'^(s\.|san|santa|santo)\s+', '', nombre, flags=re.IGNORECASE)
    if nombre_limpio != nombre:
        print(f"  Limpiado prefijo: '{nombre}' -> '{nombre_limpio}'")
        nombre = nombre_limpio
    
    # Convertir a minúsculas para comparación
    nombre_lower = nombre.lower()
    
    # Buscar en el mapeo primero
    if nombre_lower in MAPEO_LIBROS:
        return MAPEO_LIBROS[nombre_lower]
    
    # Si no está en el mapeo, capitalizar normalmente
    nombre_normalizado = ' '.join(word.capitalize() for word in nombre_lower.split())
    
    return nombre_normalizado

def es_diccionario_valido(data):
    """Verifica si los datos son un diccionario válido"""
    return isinstance(data, dict) and len(data) > 0

def ordenar_capitulos_versiculos(data):
    """Ordena capítulos y versículos numéricamente"""
    if not es_diccionario_valido(data):
        print(f"  Datos no válidos para ordenar: {type(data)}")
        return {}
    
    capitulos_ordenados = {}
    
    try:
        # Ordenar capítulos
        capitulos = list(data.keys())
        
        # Intentar ordenar numéricamente
        capitulos_numericos = []
        capitulos_no_numericos = []
        
        for cap in capitulos:
            if isinstance(cap, str) and cap.isdigit():
                capitulos_numericos.append(int(cap))
            else:
                capitulos_no_numericos.append(cap)
        
        capitulos_numericos.sort()
        capitulos_no_numericos.sort()
        
        capitulos_ordenados_lista = [str(cap) for cap in capitulos_numericos] + capitulos_no_numericos
        
        for capitulo in capitulos_ordenados_lista:
            if capitulo in data and es_diccionario_valido(data[capitulo]):
                # Ordenar versículos
                versiculos_ordenados = {}
                versiculos = list(data[capitulo].keys())
                
                versiculos_numericos = []
                versiculos_no_numericos = []
                
                for vers in versiculos:
                    if isinstance(vers, str) and vers.isdigit():
                        versiculos_numericos.append(int(vers))
                    else:
                        versiculos_no_numericos.append(vers)
                
                versiculos_numericos.sort()
                versiculos_no_numericos.sort()
                
                versiculos_ordenados_lista = [str(vers) for vers in versiculos_numericos] + versiculos_no_numericos
                
                for versiculo in versiculos_ordenados_lista:
                    if versiculo in data[capitulo]:
                        versiculos_ordenados[versiculo] = data[capitulo][versiculo]
                
                capitulos_ordenados[capitulo] = versiculos_ordenados
                
    except Exception as e:
        print(f"  Error ordenando capítulos: {e}")
        return data
    
    return capitulos_ordenados

# Cargar datos de la Biblia
def cargar_biblia():
    try:
        print("Cargando archivo RV1960.json...")
        
        with open('data/RV1960.json', 'r') as f:
            biblia_data = json.load(f)
        
        print(f"Tipo de datos cargados: {type(biblia_data)}")
        
        if not es_diccionario_valido(biblia_data):
            print("Error: El archivo JSON no contiene un diccionario válido")
            return {}
            
        print("Libros encontrados en el archivo JSON:")
        libros_originales = list(biblia_data.keys())
        for libro in libros_originales:
            print(f"  - {libro}")
        
        # Reorganizar los libros según el orden bíblico
        biblia_ordenada = {}
        libros_procesados = set()
        
        print("\nProcesando libros en orden bíblico...")
        
        # Procesar todos los libros del orden
        for testamento in ORDEN_LIBROS:
            for libro_ordenado in ORDEN_LIBROS[testamento]:
                encontrado = False
                
                # Buscar coincidencia exacta
                if libro_ordenado in biblia_data and es_diccionario_valido(biblia_data[libro_ordenado]):
                    contenido_ordenado = ordenar_capitulos_versiculos(biblia_data[libro_ordenado])
                    if contenido_ordenado:
                        biblia_ordenada[libro_ordenado] = contenido_ordenado
                        libros_procesados.add(libro_ordenado)
                        print(f"✓ Libro exacto: {libro_ordenado}")
                        encontrado = True
                        continue
                
                # Si no hay coincidencia exacta, buscar por nombres alternativos
                if not encontrado:
                    for libro_original in libros_originales:
                        if libro_original in libros_procesados:
                            continue
                            
                        libro_normalizado_original = normalizar_nombre_libro(libro_original)
                        libro_normalizado_ordenado = normalizar_nombre_libro(libro_ordenado)
                        
                        if libro_normalizado_original == libro_normalizado_ordenado:
                            if es_diccionario_valido(biblia_data[libro_original]):
                                contenido_ordenado = ordenar_capitulos_versiculos(biblia_data[libro_original])
                                if contenido_ordenado:
                                    biblia_ordenada[libro_ordenado] = contenido_ordenado
                                    libros_procesados.add(libro_original)
                                    print(f"✓ Libro mapeado: '{libro_original}' -> '{libro_ordenado}'")
                                    encontrado = True
                                    break
        
        # Procesar libros que no se encontraron en el orden
        print("\nBuscando libros no procesados...")
        for libro_original in libros_originales:
            if libro_original in libros_procesados:
                continue
                
            libro_normalizado = normalizar_nombre_libro(libro_original)
            print(f"  Procesando libro no encontrado: '{libro_original}' -> '{libro_normalizado}'")
            
            # Verificar si el libro normalizado ya está en la biblia ordenada
            ya_existe = False
            for libro_orden in biblia_ordenada.keys():
                if normalizar_nombre_libro(libro_orden) == libro_normalizado:
                    ya_existe = True
                    print(f"  ⚠️  Ya existe como: '{libro_orden}'")
                    break
            
            if not ya_existe and es_diccionario_valido(biblia_data[libro_original]):
                contenido_ordenado = ordenar_capitulos_versiculos(biblia_data[libro_original])
                if contenido_ordenado:
                    # Usar el nombre normalizado para el libro
                    biblia_ordenada[libro_normalizado] = contenido_ordenado
                    libros_procesados.add(libro_original)
                    print(f"  + Agregado: '{libro_original}' -> '{libro_normalizado}'")
        
        print(f"\n✅ Procesamiento completado")
        print(f"Total de libros procesados: {len(libros_procesados)}/{len(libros_originales)}")
        print(f"Total de libros en Biblia ordenada: {len(biblia_ordenada)}")
        
        # Mostrar el orden final
        print("\nORDEN FINAL DE LIBROS:")
        for testamento in ORDEN_LIBROS:
            print(f"\n{testamento}:")
            for i, libro in enumerate(ORDEN_LIBROS[testamento], 1):
                if libro in biblia_ordenada:
                    print(f"  {i:2d}. {libro}")
            
        return biblia_ordenada
            
    except FileNotFoundError:
        print("❌ Error: Archivo data/RV1960.json no encontrado")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error procesando la Biblia: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {}

def cargar_comentarios():
    comentarios = {}
    try:
        print("Cargando comentarios...")
        for i in range(1, 67):
            archivo = f'data/comment/{i}.json'
            if os.path.exists(archivo):
                with open(archivo, 'r') as f:
                    data = json.load(f)
                    nombre_libro = data.get('libro', '')
                    if nombre_libro:
                        nombre_normalizado = normalizar_nombre_libro(nombre_libro)
                        comentarios[nombre_normalizado] = data.get('comentarios', [])
        print(f"✓ Comentarios cargados: {len(comentarios)} libros")
    except Exception as e:
        print(f"❌ Error cargando comentarios: {e}")
    return comentarios

def cargar_cba_append():
    """Cargar el archivo de apéndices CBA"""
    try:
        print("Cargando archivo cba_append.json...")
        with open('data/cba_append.json', 'r') as f:
            cba_data = json.load(f)
        print(f"✓ CBA Append cargado: {len(cba_data)} documentos")
        return cba_data
    except FileNotFoundError:
        print("⚠️  Archivo data/cba_append.json no encontrado")
        return {}
    except Exception as e:
        print(f"❌ Error cargando CBA Append: {e}")
        return {}

def procesar_referencias(referencia_completa):
    """Procesa referencias bíblicas, completando libros implícitos"""
    if not referencia_completa:
        return []
    
    referencias = []
    referencias_raw = [ref.strip() for ref in referencia_completa.split(';') if ref.strip()]
    
    ultimo_libro = None
    
    for ref in referencias_raw:
        # Verificar si la referencia tiene libro explícito (contiene texto antes del número)
        if re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.]+\s+\d', ref):
            # Referencia con libro explícito: "S.Juan 1:1" o "Juan 1:1"
            partes = re.split(r'\s+', ref, 1)
            if len(partes) == 2:
                libro_ref = partes[0].strip()
                resto_ref = partes[1]
                
                # Normalizar el nombre del libro
                ultimo_libro = normalizar_nombre_libro(libro_ref)
                referencia_completa = f"{ultimo_libro} {resto_ref}"
                
                print(f"  Referencia procesada: '{libro_ref}' -> '{ultimo_libro}'")
        else:
            # Referencia sin libro: "1:1" - usar el último libro conocido
            if ultimo_libro:
                referencia_completa = f"{ultimo_libro} {ref}"
            else:
                # Si no hay último libro, mantener la referencia como está
                referencia_completa = ref
        
        referencias.append(referencia_completa)
    
    return referencias

# Cargar datos al iniciar
print("=" * 60)
print("INICIANDO CARGA DE BIBLIA DIGITAL")
print("=" * 60)

BIBLIA = cargar_biblia()
COMENTARIOS = cargar_comentarios()
CBA_APPEND = cargar_cba_append()

print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
print(f"📚 Libros cargados en la Biblia: {len(BIBLIA)}")
print(f"💭 Libros con comentarios: {len(COMENTARIOS)}")
print(f"📖 Documentos CBA cargados: {len(CBA_APPEND)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/libros')
def obtener_libros():
    """Retorna los libros organizados por testamento"""
    if BIBLIA:
        return jsonify(ORDEN_LIBROS)
    return jsonify({"Antiguo Testamento": [], "Nuevo Testamento": []})

@app.route('/capitulos/<libro>')
def obtener_capitulos(libro):
    libro_normalizado = normalizar_nombre_libro(libro)
    print(f"Buscando capítulos para: '{libro}' -> '{libro_normalizado}'")
    
    # Buscar libro exacto
    if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
        capitulos = list(BIBLIA[libro].keys())
        return jsonify(capitulos)
    
    # Buscar por nombre normalizado
    for libro_biblia in BIBLIA.keys():
        if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
            if es_diccionario_valido(BIBLIA[libro_biblia]):
                capitulos = list(BIBLIA[libro_biblia].keys())
                print(f"  Encontrado: '{libro_biblia}' con {len(capitulos)} capítulos")
                return jsonify(capitulos)
    
    print(f"  No encontrado: '{libro}'")
    return jsonify([])

@app.route('/versiculos/<libro>/<capitulo>')
def obtener_versiculos(libro, capitulo):
    libro_normalizado = normalizar_nombre_libro(libro)
    print(f"Buscando versículos: '{libro}' -> '{libro_normalizado}' capítulo {capitulo}")
    
    # Buscar libro exacto
    if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
        if capitulo in BIBLIA[libro] and isinstance(BIBLIA[libro][capitulo], dict):
            return jsonify(BIBLIA[libro][capitulo])
    
    # Buscar por nombre normalizado
    for libro_biblia in BIBLIA.keys():
        if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
            if es_diccionario_valido(BIBLIA[libro_biblia]):
                if capitulo in BIBLIA[libro_biblia] and isinstance(BIBLIA[libro_biblia][capitulo], dict):
                    print(f"  Encontrado en: '{libro_biblia}'")
                    return jsonify(BIBLIA[libro_biblia][capitulo])
            break
    
    print(f"  No encontrado: '{libro}' capítulo {capitulo}")
    return jsonify({})

@app.route('/comentarios/<libro>/<capitulo>/<versiculo>')
def obtener_comentario(libro, capitulo, versiculo):
    try:
        libro_normalizado = normalizar_nombre_libro(libro)
        print(f"Buscando comentario: '{libro}' -> '{libro_normalizado}' {capitulo}:{versiculo}")
        
        # Buscar comentarios para el libro normalizado
        if libro_normalizado in COMENTARIOS:
            comentarios_libro = COMENTARIOS[libro_normalizado]
            print(f"  Comentarios encontrados para: '{libro_normalizado}'")
        else:
            # Buscar por coincidencia parcial del nombre
            for nombre_libro in COMENTARIOS.keys():
                if nombre_libro.lower().startswith(libro_normalizado.lower()) or libro_normalizado.lower().startswith(nombre_libro.lower()):
                    comentarios_libro = COMENTARIOS[nombre_libro]
                    print(f"  Comentarios encontrados por coincidencia: '{nombre_libro}'")
                    break
            else:
                print(f"  No hay comentarios para: '{libro_normalizado}'")
                return jsonify({'comentario': 'No hay comentario disponible para este versículo.', 'referencia': ''})

        for comentario_capitulo in comentarios_libro:
            if str(comentario_capitulo['capitulo']) == str(capitulo):
                for comentario_versiculo in comentario_capitulo['versiculos']:
                    vers_ref = comentario_versiculo['versiculo']
                    # Manejar rangos de versículos (ej: "1-3")
                    if '-' in vers_ref:
                        try:
                            inicio, fin = map(int, vers_ref.split('-'))
                            if inicio <= int(versiculo) <= fin:
                                referencia_completa = comentario_versiculo.get('referencia', '')
                                referencias = procesar_referencias(referencia_completa)
                                
                                return jsonify({
                                    'comentario': comentario_versiculo['comentario'],
                                    'referencia': referencia_completa,
                                    'referencias_separadas': referencias
                                })
                        except ValueError:
                            continue
                    # Coincidencia exacta
                    elif str(vers_ref) == str(versiculo):
                        referencia_completa = comentario_versiculo.get('referencia', '')
                        referencias = procesar_referencias(referencia_completa)
                        
                        return jsonify({
                            'comentario': comentario_versiculo['comentario'],
                            'referencia': referencia_completa,
                            'referencias_separadas': referencias
                        })
    except Exception as e:
        print(f"Error obteniendo comentario para {libro} {capitulo}:{versiculo}: {e}")
    
    return jsonify({
        'comentario': 'No hay comentario disponible para este versículo.', 
        'referencia': '',
        'referencias_separadas': []
    })

@app.route('/cba_append')
def obtener_cba_append():
    """Retorna los datos del CBA Append"""
    return jsonify(CBA_APPEND)

@app.route('/buscar')
def buscar():
    termino = request.args.get('q', '').strip().lower()
    resultados = []
    
    if not termino or not BIBLIA:
        return jsonify(resultados)
    
    try:
        for libro, capitulos in BIBLIA.items():
            if not es_diccionario_valido(capitulos):
                continue
                
            for capitulo, versiculos in capitulos.items():
                if not isinstance(versiculos, dict):
                    continue
                    
                for num_versiculo, texto in versiculos.items():
                    if termino in texto.lower():
                        resultados.append({
                            'libro': libro,
                            'capitulo': capitulo,
                            'versiculo': num_versiculo,
                            'texto': texto
                        })
        
        resultados = resultados[:100]
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    
    return jsonify(resultados)

@app.route('/referencia/<referencia>')
def obtener_referencia(referencia):
    try:
        referencia = referencia.strip()
        print(f"Buscando referencia: '{referencia}'")
        
        patron = r'(.+?)\s+(\d+):(\d+(?:-\d+)?)'
        match = re.search(patron, referencia)
        
        if match:
            libro = match.group(1).strip()
            capitulo = match.group(2)
            versiculo_rango = match.group(3)
            
            libro_normalizado = normalizar_nombre_libro(libro)
            print(f"  Referencia parseada: '{libro}' -> '{libro_normalizado}' {capitulo}:{versiculo_rango}")
            
            # Buscar libro exacto
            if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
                libro_real = libro
                print(f"  Libro encontrado exacto: '{libro_real}'")
            else:
                # Buscar por nombre normalizado
                libro_encontrado = None
                for libro_biblia in BIBLIA.keys():
                    if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
                        if es_diccionario_valido(BIBLIA[libro_biblia]):
                            libro_encontrado = libro_biblia
                            print(f"  Libro encontrado por normalización: '{libro_biblia}'")
                            break
                
                if libro_encontrado:
                    libro_real = libro_encontrado
                else:
                    print(f"  Libro no encontrado: '{libro}' -> '{libro_normalizado}'")
                    return jsonify({'error': f'Libro "{libro}" no encontrado'})
            
            # Verificar si el capítulo existe
            if capitulo not in BIBLIA[libro_real] or not isinstance(BIBLIA[libro_real][capitulo], dict):
                return jsonify({'error': f'Capítulo {capitulo} no encontrado en {libro_real}'})
            
            # Manejar rangos de versículos
            if '-' in versiculo_rango:
                vers_inicio, vers_fin = map(int, versiculo_rango.split('-'))
                versiculos_texto = []
                
                for v in range(vers_inicio, vers_fin + 1):
                    vers_str = str(v)
                    if vers_str in BIBLIA[libro_real][capitulo]:
                        versiculos_texto.append(f"{vers_str}. {BIBLIA[libro_real][capitulo][vers_str]}")
                    else:
                        versiculos_texto.append(f"{vers_str}. [Versículo no encontrado]")
                
                texto_completo = '\n'.join(versiculos_texto)
                return jsonify({
                    'libro': libro_real,
                    'capitulo': capitulo,
                    'versiculo': versiculo_rango,
                    'texto': texto_completo,
                    'es_rango': True
                })
            else:
                # Versículo único
                if versiculo_rango in BIBLIA[libro_real][capitulo]:
                    return jsonify({
                        'libro': libro_real,
                        'capitulo': capitulo,
                        'versiculo': versiculo_rango,
                        'texto': BIBLIA[libro_real][capitulo][versiculo_rango],
                        'es_rango': False
                    })
                else:
                    return jsonify({'error': f'Versículo {versiculo_rango} no encontrado en {libro_real} {capitulo}'})
        else:
            return jsonify({'error': 'Formato de referencia inválido. Use: "Libro Capítulo:Versículo"'})
            
    except Exception as e:
        print(f"Error obteniendo referencia {referencia}: {e}")
        return jsonify({'error': 'Error procesando la referencia'})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        directory=os.path.join(app.root_path, 'data'),  # carpeta data dentro del proyecto
        path='favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)