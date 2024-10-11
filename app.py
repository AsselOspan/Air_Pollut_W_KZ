#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import geemap.foliumap as geemap
import ee

# Инициализация Earth Engine
ee.Initialize()

# Заголовок приложения
st.title("Анализ загрязнителей Западного Казахстана")

# Параметры визуализации для различных загрязнителей
viz_params = {
    "AER_AI": {"min": -1, "max": 2.0, "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'], "band": "absorbing_aerosol_index"},
    "CO": {"min": 0, "max": 0.05, "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'], "band": "CO_column_number_density"},
    "HCHO": {"min": 0.0, "max": 0.003, "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'], "band": "tropospheric_HCHO_column_number_density"},
    "NO2": {"min": 0, "max": 0.0002, "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'], "band": "NO2_column_number_density"},
    "SO2": {"min": 0.0, "max": 0.0007, "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'], "band": "SO2_column_number_density"},
    "CH4": {
        "min": 1750,
        "max": 1900,
        "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
        "band": "CH4_column_volume_mixing_ratio_dry_air",
        "product": 'COPERNICUS/S5P/OFFL/L3_CH4'
    }
}

# Загрузка региона Западного Казахстана
region = ee.FeatureCollection('projects/ee-asselyaospan/assets/KZ_West')

# Виджеты выбора параметров
year = st.slider('Выберите год', 2018, 2023, 2023)
month = st.slider('Выберите месяц', 1, 12, 7)
statistic = st.selectbox('Выберите статистику', ['min', 'mean', 'max'])
hotspot_percentage = st.slider('Порог горячих точек (%)', 0, 100, 90)

# Кнопка для отображения карты горячих точек
show_hotspots = st.checkbox('Показать горячие точки')

# Создание карты
Map = geemap.Map(center=[51.9105, 47.0921], zoom=5)

# Функция для создания отфильтрованной коллекции изображений
def create_filtered_collection(product, band, region, year, month):
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    return ee.ImageCollection(product).filterBounds(region.geometry()).filterDate(start_date, end_date).select(band)

# Функция обновления карты
def update_map(year, month, statistic, hotspot_percentage, show_hotspots):
    images = {}  # Словарь для хранения изображений
    for name, params in viz_params.items():
        product_id = params.get("product", f"COPERNICUS/S5P/NRTI/L3_{name.upper()}")
        collection = create_filtered_collection(product_id, params["band"], region, year, month)

        if statistic == 'min':
            image = collection.min().clip(region)
        elif statistic == 'mean':
            image = collection.mean().clip(region)
        elif statistic == 'max':
            image = collection.max().clip(region)

        # Добавление слоя на карту
        Map.addLayer(image, params, f"{name} {year}-{month:02d} ({statistic})")

        # Если выбраны горячие точки
        if show_hotspots:
            threshold = params['max'] * (hotspot_percentage / 100.0)
            hotspots = image.gt(threshold).selfMask()
            gradient_palette = ['purple', 'orange', 'red']
            Map.addLayer(hotspots, {"palette": gradient_palette, "opacity": 0.7}, f"{name} Hotspots")

        # Сохранение изображения для экспорта
        images[name] = image

    return images

# Функция загрузки изображений на Google Диск
def export_image_to_drive(image, description, folder='Air_Pollutants_2020'):
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region.geometry().bounds().getInfo()['coordinates'],
        scale=1000,
        fileFormat='GeoTIFF'
    )
    task.start()
    st.success(f"Экспорт {description} начат на Google Диск в папку: {folder}")

# Функция для экспорта всех изображений
def export_all_images(images):
    for name, image in images.items():
        export_image_to_drive(image, f"{name}_collection_{year}_{month:02d}")

# Обновление карты на основе выбранных параметров
images = update_map(year, month, statistic, hotspot_percentage, show_hotspots)

# Кнопка для экспорта изображений
if st.button("Экспортировать изображения на Google Диск"):
    export_all_images(images)

# Отображение карты в приложении
Map.to_streamlit(height=600)

