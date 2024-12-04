from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse, parse_qs
import os
import pandas as pd
import requests
from tqdm import tqdm
import time
import re
from bs4 import BeautifulSoup
import pickle

def normalize_url(url):
    """
    Normaliza la URL eliminando parámetros irrelevantes para evitar duplicados.
    """
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    # Eliminar parámetros irrelevantes que puedan causar duplicados
    filtered_query = {k: v for k, v in query.items() if k not in ['utm_source', 'utm_medium', 'utm_campaign', 'variant', 'ref']}
    normalized_query = '&'.join([f"{k}={v[0]}" for k, v in filtered_query.items()])
    normalized_url = parsed_url._replace(query=normalized_query).geturl()
    return normalized_url

def get_all_links(page, base_url):
    """
    Extrae todas las URLs relevantes desde la página, incluyendo categorías, productos y páginas de paginación.
    :param base_url: La URL base proporcionada por el usuario.
    """
    all_links = []
    link_elements = page.query_selector_all("a")  # Buscar todos los enlaces
    for link in link_elements:
        href = link.get_attribute("href")
        if href and ("/collections/" in href or "/products/" in href or "page=" in href):
            full_url = urljoin(base_url, href)
            normalized_url = normalize_url(full_url)
            all_links.append(normalized_url)  # Usar urljoin con base_url
    return list(set(all_links))  # Eliminar duplicados

def scrape_product_details(browser, product_url, images_folder, output_file, scraped_products):
    """
    Extrae detalles específicos de un producto individual, incluyendo tallas.
    """
    if product_url in scraped_products:
        return  # Evitar procesar el mismo producto varias veces

    product_page = browser.new_page()
    product_page.goto(product_url)
    product_page.wait_for_load_state("domcontentloaded")  # Esperar a que la página cargue completamente

    try:
        # Extraer título, descripción y precio
        title = product_page.query_selector("meta[property='og:title']").get_attribute("content")
        description = product_page.query_selector("meta[property='og:description']").get_attribute("content")
        price_element = product_page.query_selector("[data-product-price], .price, .product-price")
        price = price_element.inner_text().strip() if price_element else None

        # Extraer número de referencia
        reference_element = product_page.query_selector(".product-single__sku, .product-reference, [itemprop='sku'], .sku")
        reference = reference_element.inner_text().strip().replace("Referencia: ", "") if reference_element else title.replace(" ", "_")

        # Extraer tallas
        size_elements = product_page.query_selector_all("select#SingleOptionSelector-template--option-0 option")
        sizes_list = [size.inner_text().strip() for size in size_elements] if size_elements else []
        sizes_text = ", ".join(sizes_list)

        # Descargar todas las imágenes del producto
        image_elements = product_page.query_selector_all(".product__thumb-item img, img[src*='cdn.shopify.com'], img.product-gallery__image, img.product-single__photo")
        for idx, img_elem in enumerate(image_elements, start=1):
            image_url = img_elem.get_attribute("src")
            if image_url:
                # Asegurarse de que la URL de la imagen sea absoluta
                image_url = urljoin(product_url, image_url)
                ext = os.path.splitext(image_url.split("?")[0])[-1]  # Evitar parámetros en la URL
                image_name = f"{title.replace(' ', '_')}_{idx}{ext}"
                image_path = os.path.join(images_folder, image_name)
                img_data = requests.get(image_url).content
                with open(image_path, "wb") as img_file:
                    img_file.write(img_data)

        product_details = {
            "Título": title,
            "Descripción": description,
            "Precio": price,
            "Número de Referencia": reference,
            "Tallas": sizes_text,
            "URL Producto": product_url,
        }

        # Escribir los detalles en el archivo de salida
        df = pd.DataFrame([product_details])
        df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)
        scraped_products.add(product_url)  # Agregar el producto a la lista de procesados

    except Exception as e:
        print(f"Error procesando el producto {product_url}: {e}")
    finally:
        product_page.close()

def scrape_shopify_exhaustively(url, output_dir, delay=2, max_depth=3):
    """
    Scraper principal que recorre toda la tienda exhaustivamente.
    """
    images_folder = os.path.join(output_dir, "product_images")
    os.makedirs(images_folder, exist_ok=True)
    output_file = os.path.join(output_dir, "productos.csv")
    cache_file = os.path.join(output_dir, "product_links_cache.pkl")
    visited_links = set()
    to_visit_links = [(url, 0)]  # Agregar profundidad inicial
    product_links = set()
    scraped_products = set()

    # Cargar el caché de enlaces de productos si existe
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            product_links = pickle.load(f)
        print(f"Cargado caché de {len(product_links)} enlaces de productos.")
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            total_links = len(to_visit_links)

            # Paso preliminar: recolectar todos los enlaces de productos sin duplicados
            with tqdm(total=total_links, desc="Recolectando enlaces", unit="link") as pbar:
                while to_visit_links:
                    current_url, depth = to_visit_links.pop(0)
                    normalized_current_url = normalize_url(current_url)
                    if normalized_current_url in visited_links or depth > max_depth:
                        pbar.update(1)
                        continue

                    page = browser.new_page()
                    try:
                        page.goto(current_url)
                        page.wait_for_load_state("domcontentloaded")  # Esperar a que la página cargue completamente
                        visited_links.add(normalized_current_url)
                        pbar.set_description(f"Analizando: {current_url}")

                        # Extraer todos los enlaces de la página actual
                        new_links = get_all_links(page, url)
                        for link in new_links:
                            normalized_link = normalize_url(link)
                            if normalized_link not in visited_links and "/products/" in normalized_link:
                                product_links.add(normalized_link)
                            elif normalized_link not in visited_links and ("/collections/" in normalized_link or "page=" in normalized_link):
                                # Aumentar la profundidad solo si es una colección o página
                                to_visit_links.append((link, depth + 1 if "/collections/" in link else depth))
                                total_links += 1
                                pbar.total = total_links
                                pbar.refresh()
                    except Exception as e:
                        print(f"Error procesando la URL {current_url}: {e}")
                    finally:
                        page.close()
                    pbar.update(1)
                    time.sleep(delay)  # Añadir un retraso entre solicitudes si es necesario

            # Guardar los enlaces de productos en el caché
            with open(cache_file, 'wb') as f:
                pickle.dump(product_links, f)
            browser.close()

    # Realizar scraping de detalles de los productos únicos
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        with tqdm(total=len(product_links), desc="Obteniendo datos de productos", unit="producto") as pbar:
            for product_url in product_links:
                scrape_product_details(browser, product_url, images_folder, output_file, scraped_products)
                pbar.update(1)
                time.sleep(delay)

        browser.close()

    print(f"Scraping completado. Archivo CSV guardado en {output_file}")
    print(f"Imágenes almacenadas en {images_folder}")

def main():
    # Configuración básica
    import argparse
    parser = argparse.ArgumentParser(description="Scraper exhaustivo para Shopify.")
    parser.add_argument("--url", required=True, help="URL base de la tienda.")
    parser.add_argument("--output", default="resultados", help="Directorio de salida.")
    parser.add_argument("--delay", type=int, default=2, help="Delay entre solicitudes.")
    parser.add_argument("--max_depth", type=int, default=3, help="Profundidad máxima para recorrer la tienda.")
    args = parser.parse_args()

    scrape_shopify_exhaustively(args.url, args.output, args.delay, args.max_depth)

if __name__ == "__main__":
    main()
