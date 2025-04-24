import os
import django

# ВАЖНО: настройка должна быть ДО импортов из Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project2.settings')
django.setup()

import json
from app.models import Surah, Ayah


# Открываем файл quran_data.json
with open('quran_data.json', 'r', encoding='utf-8') as file:
    quran_data = json.load(file)

# Счётчик для номеров сур
surah_number = 1

# Проходим по каждой суре в JSON
for surah_data in quran_data:
    # Создаем или находим суру по имени и присваиваем номер
    surah, created = Surah.objects.get_or_create(
        name=surah_data['name'],
        defaults={'number': surah_number}  # Присваиваем номер только при создании
    )

    # Если сура уже существует, обновляем её номер, если он не был установлен
    if not created and surah.number is None:
        surah.number = surah_number
        surah.save()

    # Для каждой суры добавляем аяты
    for ayah_data in surah_data['ayahs']:
        # Создаем аят
        ayah = Ayah.objects.create(
            surah=surah,
            number=ayah_data['id'],  # Используем id как номер аята
            text=ayah_data['text'],
            transcription=ayah_data['transcription']
        )

    # Увеличиваем номер для следующей суры
    surah_number += 1
print("Аяты и суры успешно добавлены")