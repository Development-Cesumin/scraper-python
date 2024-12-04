# Scraper Exhaustivo para Shopify

Este proyecto es un scraper diseñado para extraer exhaustivamente información de productos desde tiendas en Shopify. Utiliza Playwright para la navegación y BeautifulSoup para la extracción de datos. Los detalles del producto, como el nombre, precio, descripción y tallas, se almacenan en un archivo CSV, y las imágenes de los productos se descargan en una carpeta específica.

## Requisitos

Para ejecutar este scraper, necesitas instalar los siguientes paquetes de Python:

- [Playwright](https://playwright.dev/python/docs/intro): Navegación web para automatizar el scraping.
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/): Analizador HTML para extraer información de las páginas.
- [Pandas](https://pandas.pydata.org/): Para la manipulación y almacenamiento de datos en formato CSV.
- [Requests](https://pypi.org/project/requests/): Para descargar imágenes.
- [Tqdm](https://github.com/tqdm/tqdm): Para mostrar barras de progreso durante la ejecución.

Puedes instalar todos los paquetes necesarios utilizando el archivo `requirements.txt`:

```sh
pip install -r requirements.txt
```

## Uso

Este script se ejecuta a través de la línea de comandos. Utiliza Playwright para recorrer exhaustivamente las páginas de productos y colecciones de una tienda Shopify.

### Sintaxis del comando

```sh
python scraper.py --url [URL_BASE] --output [DIRECTORIO_DE_SALIDA] --delay [DELAY] --max_depth [PROFUNDIDAD_MAXIMA]
```

### Parámetros

- `--url` (obligatorio): La URL base de la tienda Shopify que deseas extraer.
- `--output` (opcional): El directorio donde se almacenarán los resultados (por defecto es `resultados`).
- `--delay` (opcional): El tiempo en segundos entre cada solicitud para evitar ser bloqueado (por defecto es `2`).
- `--max_depth` (opcional): La profundidad máxima para recorrer la tienda (por defecto es `3`).

### Ejemplo

```sh
python scraper.py --url https://ejemplo.myshopify.com --output resultados --delay 3 --max_depth 2
```

Este comando extraerá los productos de la tienda en la URL proporcionada, guardando la información en el directorio `resultados`, con un retraso de `3` segundos entre solicitudes y una profundidad máxima de `2`.

## Funcionalidades

- **Normalización de URLs**: Se eliminan parámetros irrelevantes (como `utm_source`, `utm_medium`, etc.) para evitar duplicación de enlaces.
- **Extracción de enlaces**: Recorre la tienda para encontrar todos los enlaces relevantes a colecciones y productos, así como páginas de paginación.
- **Scraping de detalles de productos**: Extrae información detallada de cada producto, como título, descripción, precio, número de referencia y tallas disponibles.
- **Descarga de imágenes**: Descarga las imágenes de los productos y las guarda con nombres descriptivos.
- **Uso de caché**: Utiliza un caché basado en `pickle` para evitar volver a procesar enlaces de productos ya visitados, mejorando la eficiencia.

## Salida

El script genera:

1. Un archivo CSV (`productos.csv`) que contiene la información de los productos extraídos, incluyendo el título, descripción, precio, número de referencia, tallas y URL del producto.
2. Una carpeta (`product_images`) que contiene las imágenes descargadas de los productos.

## Notas

- Asegúrate de respetar las políticas de uso de la tienda y de Shopify. Este script está destinado solo para fines educativos y de investigación.
- Puede ser necesario ajustar el valor de `delay` para evitar sobrecargar los servidores de la tienda y ser bloqueado.

## Dependencias

Este proyecto requiere Python 3.7 o superior. Instala Playwright siguiendo las instrucciones de su [documentación oficial](https://playwright.dev/python/docs/intro).

## Licencia

Este proyecto está bajo la Licencia MIT. Por favor revisa el archivo `LICENSE` para más detalles.

