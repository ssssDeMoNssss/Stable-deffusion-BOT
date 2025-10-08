#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import subprocess
import logging
import time
import psutil

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def find_bot_processes():
    """Находит все запущенные процессы бота."""
    bot_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Проверяем, что это процесс Python, запускающий bot.py
            if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                cmdline = proc.info['cmdline']
                if cmdline and any('bot.py' in cmd for cmd in cmdline):
                    bot_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return bot_processes

def stop_bot():
    """Останавливает все запущенные экземпляры бота."""
    bot_processes = find_bot_processes()
    
    if not bot_processes:
        logger.info("Не найдено запущенных экземпляров бота.")
        return
    
    logger.info(f"Найдено {len(bot_processes)} запущенных экземпляров бота.")
    
    for proc in bot_processes:
        try:
            logger.info(f"Останавливаю процесс с PID {proc.pid}...")
            proc.terminate()
        except Exception as e:
            logger.error(f"Ошибка при остановке процесса {proc.pid}: {e}")
    
    # Даем процессам время на корректное завершение
    time.sleep(2)
    
    # Проверяем, остались ли процессы, и принудительно завершаем их
    for proc in bot_processes:
        try:
            if proc.is_running():
                logger.warning(f"Процесс {proc.pid} все еще работает. Принудительное завершение...")
                proc.kill()
        except Exception as e:
            logger.error(f"Ошибка при принудительном завершении процесса {proc.pid}: {e}")
    
    logger.info("Все экземпляры бота остановлены.")

def start_bot():
    """Запускает бота в фоновом режиме."""
    # Проверяем, нет ли уже запущенных экземпляров
    bot_processes = find_bot_processes()
    if bot_processes:
        logger.warning(f"Обнаружено {len(bot_processes)} запущенных экземпляров бота.")
        choice = input("Остановить существующие экземпляры и запустить новый? (y/n): ")
        if choice.lower() == 'y':
            stop_bot()
        else:
            logger.info("Запуск отменен.")
            return
    
    try:
        # Запускаем бота в фоновом режиме
        bot_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.py')
        
        # Создаем лог-файл для вывода бота
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.log')
        log_file = open(log_file_path, 'a')
        
        # Запускаем процесс
        process = subprocess.Popen(
            [sys.executable, bot_script_path],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True
        )
        
        logger.info(f"Бот запущен с PID {process.pid}. Вывод перенаправлен в {log_file_path}")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def check_status():
    """Проверяет статус запущенных экземпляров бота."""
    bot_processes = find_bot_processes()
    
    if not bot_processes:
        logger.info("Не найдено запущенных экземпляров бота.")
        return
    
    logger.info(f"Найдено {len(bot_processes)} запущенных экземпляров бота:")
    for i, proc in enumerate(bot_processes, 1):
        try:
            # Получаем информацию о процессе
            process_info = proc.as_dict(attrs=['pid', 'cpu_percent', 'memory_percent', 'create_time'])
            create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(process_info['create_time']))
            
            logger.info(f"Экземпляр {i}:")
            logger.info(f"  PID: {process_info['pid']}")
            logger.info(f"  Время запуска: {create_time}")
            logger.info(f"  Использование CPU: {process_info['cpu_percent']}%")
            logger.info(f"  Использование памяти: {process_info['memory_percent']:.2f}%")
        except Exception as e:
            logger.error(f"Ошибка при получении информации о процессе {proc.pid}: {e}")

def print_help():
    """Выводит справку по использованию скрипта."""
    print("Использование:")
    print("  python manage_bot.py start   - Запустить бота")
    print("  python manage_bot.py stop    - Остановить все экземпляры бота")
    print("  python manage_bot.py status  - Проверить статус запущенных экземпляров")
    print("  python manage_bot.py help    - Показать эту справку")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_bot()
    elif command == 'stop':
        stop_bot()
    elif command == 'status':
        check_status()
    elif command == 'help':
        print_help()
    else:
        print(f"Неизвестная команда: {command}")
        print_help()

if __name__ == "__main__":
    main()
