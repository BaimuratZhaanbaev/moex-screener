import json
import pytest
import httpx
from src.api.client import MoexClient, MoexAPIError

pytestmark = pytest.mark.unit

def test_missing_fixture_file_throws_error():
    """Проверяем, что если файла фикстуры нет на диске, выбрасывается MoexAPIError."""
    client = MoexClient()
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_fixture("this_file_does_not_exist_12345.json")
        
    assert "не найден на диске" in str(exc_info.value)

def test_fetch_from_valid_fixture(load_fixture):
    """Проверяем, что клиент успешно читает и валидирует правильную фикстуру."""
    client = MoexClient()
    
    # Загружаем данные через фикстуру-фабрику
    data = load_fixture("securities_valid.json")
    validated_data = client.validate_and_parse(data)
    
    # Проверяем, что ключевые блоки на месте
    assert "securities" in validated_data
    assert "marketdata" in validated_data
    assert validated_data["securities"]["columns"][0] == "SECID"
    assert validated_data["marketdata"]["columns"][0] == "SECID"

def test_fetch_from_empty_fixture(load_fixture):
    """Проверяем, что пустая фикстура (но с колонками) проходит валидацию,"""
    # по ТЗ пустой результат — тоже результат (например, выходной на бирже)
    client = MoexClient()
    data = load_fixture("securities_empty.json")
    validated_data = client.validate_and_parse(data)
    
    assert len(validated_data["securities"]["data"]) == 0

def test_corrupted_json_throws_error():
    """Проверяем, что при поврежденном JSON клиент выбрасывает MoexAPIError."""
    client = MoexClient()
    
    # Метод fetch_from_fixture должен поймать ошибку парсинга и выдать MoexAPIError
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_fixture("securities_corrupted.json")
    
    assert "содержит некорректный JSON" in str(exc_info.value)

def test_missing_blocks_throws_error(load_fixture):
    """Проверяем валидатор: если в JSON нет блока marketdata, должна быть ошибка."""
    client = MoexClient()
    data = load_fixture("securities_missing_marketdata.json")    

    with pytest.raises(MoexAPIError) as exc_info:
        client.validate_and_parse(data)
        
    assert "отсутствует блок 'marketdata'" in str(exc_info.value)

def test_missing_securities_throws_error(load_fixture):
    """Проверяем валидатор: если в JSON нет блока securities, должна быть ошибка."""
    client = MoexClient()
    
    # Загружаем новый JSON, где нет блока securities
    data = load_fixture("marketdata_missing_securities.json")
    
    # Ждем, что валидатор выбросит MoexAPIError
    with pytest.raises(MoexAPIError) as exc_info:
        client.validate_and_parse(data)
        
    # Проверяем, что в тексте ошибки четко написано, чего именно не хватает
    assert "отсутствует блок 'securities'" in str(exc_info.value)

def test_get_clean_data_pipeline_success(mocker, real_api_data):
    """Проверяем полный цикл конвейера (загрузка + валидация) через get_clean_data."""
    client = MoexClient()
    #data = client.get_clean_data(use_fixture="securities_valid.json")

    # Мокаем httpx.get, чтобы он вернул реальный JSON
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = b""
    mock_response.json.return_value = real_api_data
    mocker.patch("httpx.get", return_value=mock_response)
    
    # Вызываем главный метод без параметров (он пойдет в "сеть", то есть в наш мок)
    result = client.get_clean_data()
    
    # Проверяем, что конвейер успешно проглотил и валидировал реальный файл
    assert result == real_api_data
    assert "securities" in result
    assert "marketdata" in result

def test_fetch_from_api_success(mocker, real_api_data):
    """Проверяем успешный сетевой запрос, подменяя httpx.get реальными данными."""
    client = MoexClient()
    
    # Создаем фальшивый ответ от сервера
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = b""
    # Вместо пустой заглушки возвращаем содержимое реального файла
    mock_response.json.return_value = real_api_data
    
    # Подменяем httpx.get
    mocker.patch("httpx.get", return_value=mock_response)
    
    result = client.fetch_from_api()
    
    # Теперь мы проверяем, что метод вернул именно структуру нашего реального файла
    assert result == real_api_data
    assert "securities" in result

def test_fetch_from_api_timeout(mocker):
    """Проверяем, что при таймауте сети fetch_from_api оборачивает его в MoexAPIError."""
    client = MoexClient()
    
    # Заставляем httpx.get выбрасывать исключение таймаута
    mocker.patch("httpx.get", side_effect=httpx.TimeoutException("Timeout"))
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_api()
        
    assert "Превышено время ожидания" in str(exc_info.value)

def test_fetch_from_api_http_status_error(mocker):
    """Проверяем обработку ошибок HTTP (например, 404 или 500 от сервера)."""
    client = MoexClient()
    
    # Имитируем объект ответа с ошибкой сервера
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.content = b""
    
    # raise_for_status должен выбросить HTTPStatusError
    error = httpx.HTTPStatusError("Server Error", request=mocker.Mock(), response=mock_response)
    mock_response.raise_for_status.side_effect = error
    
    mocker.patch("httpx.get", return_value=mock_response)
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_api()
        
    assert "Ошибка сервера MOEX" in str(exc_info.value)

def test_fetch_from_api_request_error(mocker):
    """Проверяем общую сетевую ошибку (проблемы с подключением)."""
    client = MoexClient()
    
    # Заставляем httpx.get выбросить ошибку запроса
    error = httpx.RequestError("Connection refused", request=mocker.Mock())
    mocker.patch("httpx.get", side_effect=error)
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_api()
        
    assert "Сетевая ошибка: проверьте подключение" in str(exc_info.value)

def test_fetch_from_api_invalid_json(mocker):
    """Проверяем, что если сервер вернул не JSON, падает правильная ошибка."""
    client = MoexClient()
    
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = b""
    # Заставляем метод .json() выбросить ошибку парсинга
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    
    mocker.patch("httpx.get", return_value=mock_response)
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_api()
        
    assert "Получен некорректный JSON-пакет" in str(exc_info.value)

def test_fetch_from_api_unexpected_exception(mocker):
    """Проверяем обработку абсолютно любой непредвиденной ошибки."""
    client = MoexClient()
    
    # Выбрасываем стандартный ValueError, который не ловится специфичными except
    mocker.patch("httpx.get", side_effect=ValueError("Что-то пошло совсем не так"))
    
    with pytest.raises(MoexAPIError) as exc_info:
        client.fetch_from_api()
        
    assert "Произошла непредвиденная ошибка" in str(exc_info.value)
    assert "ValueError" in str(exc_info.value)