from flask import Flask, render_template, request, jsonify, send_from_directory
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
        
        with open('data/RV1960.json', 'r', encoding='utf-8') as f:
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
            
            # Verificar si el libro normalizado ya está en la biblia ordenada
            ya_existe = False
            for libro_orden in biblia_ordenada.keys():
                if normalizar_nombre_libro(libro_orden) == libro_normalizado:
                    ya_existe = True
                    break
            
            if not ya_existe and es_diccionario_valido(biblia_data[libro_original]):
                contenido_ordenado = ordenar_capitulos_versiculos(biblia_data[libro_original])
                if contenido_ordenado:
                    # Usar el nombre normalizado para el libro
                    biblia_ordenada[libro_normalizado] = contenido_ordenado
                    libros_procesados.add(libro_original)
        
        print(f"\n✅ Procesamiento completado")
        print(f"Total de libros procesados: {len(libros_procesados)}/{len(libros_originales)}")
        print(f"Total de libros en Biblia ordenada: {len(biblia_ordenada)}")
            
        return biblia_ordenada
            
    except FileNotFoundError:
        print("❌ Error: Archivo data/RV1960.json no encontrado")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error procesando la Biblia: {e}")
        return {}

def cargar_comentarios():
    comentarios = {}
    try:
        print("Cargando comentarios principales...")
        for i in range(1, 67):
            archivo = f'data/comment/{i}.json'
            if os.path.exists(archivo):
                try:
                    with open(archivo, 'r') as f:
                        data = json.load(f)
                        nombre_libro = data.get('libro', '')
                        if nombre_libro:
                            nombre_normalizado = normalizar_nombre_libro(nombre_libro)
                            comentarios[nombre_normalizado] = data.get('comentarios', [])
                            print(f"  ✓ {nombre_normalizado}")
                except Exception as e:
                    print(f"  ❌ Error cargando {archivo}: {e}")
        
        print(f"✅ Comentarios principales cargados: {len(comentarios)} libros")
        return comentarios
        
    except Exception as e:
        print(f"❌ Error cargando comentarios: {e}")
        return {}

def cargar_comentarios_cba():
    """Cargar solo los comentarios del CBA en una estructura separada"""
    comentarios_cba = {}
    try:
        print("Cargando comentarios CBA para ampliación...")
        archivo_cba = 'data/cba.json'
        if os.path.exists(archivo_cba):
            with open(archivo_cba, 'r') as f:
                cba_data = json.load(f)
            
            for libro, capitulos in cba_data.items():
                if libro and isinstance(capitulos, dict):
                    libro_normalizado = normalizar_nombre_libro(libro)
                    comentarios_cba[libro_normalizado] = capitulos
                    print(f"  ✓ CBA: {libro_normalizado}")
            
            print(f"✅ Comentarios CBA cargados: {len(comentarios_cba)} libros")
        else:
            print("⚠️  Archivo data/cba.json no encontrado")
            
    except Exception as e:
        print(f"❌ Error cargando comentarios CBA: {e}")
    
    return comentarios_cba

def cargar_cba_append():
    """Cargar el archivo de apéndices CBA"""
    try:
        print("Cargando archivo cba_append.json...")
        with open('data/cba_append.json', 'r') as f:
            cba_data = json.load(f)
        print(f"✅ CBA Append cargado: {len(cba_data)} documentos")
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
COMENTARIOS_CBA = cargar_comentarios_cba()
CBA_APPEND = cargar_cba_append()

print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
print(f"📚 Libros cargados en la Biblia: {len(BIBLIA)}")
print(f"💭 Libros con comentarios principales: {len(COMENTARIOS)}")
print(f"📖 Comentarios CBA cargados: {len(COMENTARIOS_CBA)}")
print(f"📋 Documentos CBA cargados: {len(CBA_APPEND)}")

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
    
    # Buscar libro exacto
    if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
        capitulos = list(BIBLIA[libro].keys())
        return jsonify(capitulos)
    
    # Buscar por nombre normalizado
    for libro_biblia in BIBLIA.keys():
        if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
            if es_diccionario_valido(BIBLIA[libro_biblia]):
                capitulos = list(BIBLIA[libro_biblia].keys())
                return jsonify(capitulos)
    
    return jsonify([])

@app.route('/versiculos/<libro>/<capitulo>')
def obtener_versiculos(libro, capitulo):
    libro_normalizado = normalizar_nombre_libro(libro)
    
    # Buscar libro exacto
    if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
        if capitulo in BIBLIA[libro] and isinstance(BIBLIA[libro][capitulo], dict):
            return jsonify(BIBLIA[libro][capitulo])
    
    # Buscar por nombre normalizado
    for libro_biblia in BIBLIA.keys():
        if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
            if es_diccionario_valido(BIBLIA[libro_biblia]):
                if capitulo in BIBLIA[libro_biblia] and isinstance(BIBLIA[libro_biblia][capitulo], dict):
                    return jsonify(BIBLIA[libro_biblia][capitulo])
            break
    
    return jsonify({})

@app.route('/comentarios/<libro>/<capitulo>/<versiculo>')
def obtener_comentario(libro, capitulo, versiculo):
    try:
        libro_normalizado = normalizar_nombre_libro(libro)
        print(f"Buscando comentario: '{libro}' -> '{libro_normalizado}' {capitulo}:{versiculo}")
        
        comentario_principal = ""
        referencia_principal = ""
        referencias_separadas_principal = []
        
        # 1. BUSCAR EN COMENTARIOS PRINCIPALES (data/comment/)
        comentario_encontrado_principal = False
        if libro_normalizado in COMENTARIOS:
            comentarios_libro = COMENTARIOS[libro_normalizado]
            
            for comentario_capitulo in comentarios_libro:
                if str(comentario_capitulo['capitulo']) == str(capitulo):
                    for comentario_versiculo in comentario_capitulo['versiculos']:
                        vers_ref = comentario_versiculo['versiculo']
                        
                        # Manejar rangos de versículos
                        if '-' in vers_ref:
                            try:
                                inicio, fin = map(int, vers_ref.split('-'))
                                if inicio <= int(versiculo) <= fin:
                                    comentario_principal = comentario_versiculo.get('comentario', '')
                                    referencia_principal = comentario_versiculo.get('referencia', '')
                                    # PROCESAR REFERENCIAS DEL COMENTARIO PRINCIPAL
                                    if referencia_principal:
                                        referencias_separadas_principal = procesar_referencias(referencia_principal)
                                    else:
                                        referencias_separadas_principal = []
                                    comentario_encontrado_principal = True
                                    print(f"  ✅ Encontrado comentario principal para rango {vers_ref}")
                                    break
                            except ValueError:
                                continue
                        # Coincidencia exacta
                        elif str(vers_ref) == str(versiculo):
                            comentario_principal = comentario_versiculo.get('comentario', '')
                            referencia_principal = comentario_versiculo.get('referencia', '')
                            # PROCESAR REFERENCIAS DEL COMENTARIO PRINCIPAL
                            if referencia_principal:
                                referencias_separadas_principal = procesar_referencias(referencia_principal)
                            else:
                                referencias_separadas_principal = []
                            comentario_encontrado_principal = True
                            print(f"  ✅ Encontrado comentario principal para versículo {vers_ref}")
                            break
        
        # 2. BUSCAR EN COMENTARIOS CBA (data/cba.json)
        comentario_cba = ""
        referencias_cba = []
        comentario_encontrado_cba = False
        
        if libro_normalizado in COMENTARIOS_CBA:
            capitulos_cba = COMENTARIOS_CBA[libro_normalizado]
            if str(capitulo) in capitulos_cba:
                versiculos_cba = capitulos_cba[str(capitulo)]
                
                for versiculo_ref, datos_versiculo in versiculos_cba.items():
                    if isinstance(datos_versiculo, dict):
                        # Manejar rangos de versículos en CBA
                        if '-' in versiculo_ref:
                            try:
                                inicio, fin = map(int, versiculo_ref.split('-'))
                                if inicio <= int(versiculo) <= fin:
                                    comentarios_lista = datos_versiculo.get('comentarios', [])
                                    if comentarios_lista:
                                        comentario_cba = " ".join(str(c) for c in comentarios_lista)
                                        comentario_encontrado_cba = True
                                    referencias = datos_versiculo.get('referencias_cruzadas', [])
                                    for ref in referencias:
                                        if ref and ref.strip():
                                            referencias_cba.extend(procesar_referencias(str(ref)))
                                    print(f"  ✅ Encontrado comentario CBA para rango {versiculo_ref}")
                                    break
                            except ValueError:
                                continue
                        # Coincidencia exacta en CBA
                        elif str(versiculo_ref) == str(versiculo):
                            comentarios_lista = datos_versiculo.get('comentarios', [])
                            if comentarios_lista:
                                comentario_cba = " ".join(str(c) for c in comentarios_lista)
                                comentario_encontrado_cba = True
                            referencias = datos_versiculo.get('referencias_cruzadas', [])
                            for ref in referencias:
                                if ref and ref.strip():
                                    referencias_cba.extend(procesar_referencias(str(ref)))
                            print(f"  ✅ Encontrado comentario CBA para versículo {versiculo_ref}")
                            break
        
        # 3. FUSIONAR COMENTARIOS DE FORMA ELEGANTE
        comentario_final = ""
        referencias_finales = referencias_separadas_principal.copy()
        
        if comentario_encontrado_principal and comentario_encontrado_cba:
            # AMBOS EXISTEN: Fusionar con formato bonito
            comentario_final = f"{comentario_principal}\n\n[CBA]\n{comentario_cba}"
            print(f"  🔄 Fusionando comentarios: Principal + CBA")
            
        elif comentario_encontrado_principal and not comentario_encontrado_cba:
            # SOLO PRINCIPAL
            comentario_final = comentario_principal
            print(f"  📚 Usando solo comentario principal")
            
        elif not comentario_encontrado_principal and comentario_encontrado_cba:
            # SOLO CBA: Usar CBA como principal
            comentario_final = f"[CBA]\n{comentario_cba}"
            print(f"  📖 Usando solo comentario CBA")
            
        else:
            # NINGUNO
            comentario_final = 'No hay comentario disponible para este versículo.'
            print(f"  ❌ No hay comentarios disponibles")
        
        # Combinar referencias
        referencias_finales.extend(referencias_cba)
        referencias_finales = list(set(referencias_finales))  # Eliminar duplicados
        
        # Combinar referencia principal
        referencia_final = referencia_principal
        if referencias_cba:
            if referencia_final:
                referencia_final += "; " + "; ".join(referencias_cba)
            else:
                referencia_final = "; ".join(referencias_cba)
        
        print(f"  📋 Referencias finales: {referencias_finales}")
        
        return jsonify({
            'comentario': comentario_final,
            'referencia': referencia_final,
            'referencias_separadas': referencias_finales,
            'fuentes': {
                'principal': comentario_encontrado_principal,
                'cba': comentario_encontrado_cba
            }
        })
            
    except Exception as e:
        print(f"Error obteniendo comentario para {libro} {capitulo}:{versiculo}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    return jsonify({
        'comentario': 'No hay comentario disponible para este versículo.', 
        'referencia': '',
        'referencias_separadas': [],
        'fuentes': {'principal': False, 'cba': False}
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
        print(f"🔍 Buscando término: '{termino}'")
        
        for libro, capitulos in BIBLIA.items():
            if not es_diccionario_valido(capitulos):
                continue
                
            for capitulo, versiculos in capitulos.items():
                if not isinstance(versiculos, dict):
                    continue
                    
                for num_versiculo, texto in versiculos.items():
                    texto_versiculo = str(texto).lower() if texto else ""
                    if termino in texto_versiculo:
                        resultados.append({
                            'libro': libro,
                            'capitulo': capitulo,
                            'versiculo': num_versiculo,
                            'texto': texto
                        })
                        print(f"  ✅ Encontrado en {libro} {capitulo}:{num_versiculo}")
        
        # Limitar resultados para no sobrecargar
        resultados = resultados[:200]
        print(f"📊 Búsqueda completada: {len(resultados)} resultados encontrados")
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    return jsonify(resultados)

@app.route('/referencia/<referencia>')
def obtener_referencia(referencia):
    try:
        referencia = referencia.strip()
        
        patron = r'(.+?)\s+(\d+):(\d+(?:-\d+)?)'
        match = re.search(patron, referencia)
        
        if match:
            libro = match.group(1).strip()
            capitulo = match.group(2)
            versiculo_rango = match.group(3)
            
            libro_normalizado = normalizar_nombre_libro(libro)
            
            # Buscar libro exacto
            if libro in BIBLIA and es_diccionario_valido(BIBLIA[libro]):
                libro_real = libro
            else:
                # Buscar por nombre normalizado
                libro_encontrado = None
                for libro_biblia in BIBLIA.keys():
                    if normalizar_nombre_libro(libro_biblia) == libro_normalizado:
                        if es_diccionario_valido(BIBLIA[libro_biblia]):
                            libro_encontrado = libro_biblia
                            break
                
                if libro_encontrado:
                    libro_real = libro_encontrado
                else:
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
        directory=os.path.join(app.root_path, 'data'),
        path='favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)
