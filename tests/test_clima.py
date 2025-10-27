import pytest
from src.clima import extraer_ciudad, obtener_clima
from requests.exceptions import HTTPError


# Test de extracción de ciudad
def test_extraer_ciudad():
    # Casos simples
    assert extraer_ciudad("¿Qué tal el clima en Madrid?") == "Madrid"
    assert extraer_ciudad("Dime el clima de París") == "París"
    assert extraer_ciudad("Hace frío en Nueva York hoy") == "Nueva York"
    
    # Caso sin ciudad
    assert extraer_ciudad("¿Qué hora es?") is None

    # Ciudad con caracteres especiales
    assert extraer_ciudad("Quiero saber el clima en São Paulo") == "São Paulo"
    assert extraer_ciudad("Dime el clima de Los Ángeles") == "Los Ángeles"



# Test de obtención de clima
def test_obtener_clima(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self._json = json_data
            self.status_code = status_code
        def json(self):
            return self._json
        def raise_for_status(self):
            if self.status_code != 200:
                raise HTTPError("HTTP Error")

    def mock_get(*args, **kwargs):
        return MockResponse({
            "cod": 200,
            "main": {"temp": 20, "humidity": 50},
            "weather": [{"description": "soleado"}],
            "wind": {"speed": 5}
        }, 200)

    monkeypatch.setattr("requests.get", mock_get)

    resultado = obtener_clima("en Madrid")
    assert "Madrid" in resultado
    assert "20" in resultado
    assert "soleado" in resultado

    resultado_sin_ciudad = obtener_clima("¿Qué hora es?")
    assert "No pude detectar la ciudad" in resultado_sin_ciudad


from src.clima import recomendacion_ropa

def test_recomendacion_ropa():
    # Frío intenso
    resultado = recomendacion_ropa(5, "nieve ligera")
    assert " Abrígate" in resultado
    assert "❄️" in resultado

    # Temperatura fresca
    resultado = recomendacion_ropa(15, "soleado")
    assert "chaqueta ligera" in resultado

    # Temperatura templada
    resultado = recomendacion_ropa(22, "soleado")
    assert " Ropa cómoda" in resultado

    # Calor
    resultado = recomendacion_ropa(30, "soleado")
    assert "calor" in resultado or "fresca" in resultado

    # Lluvia
    resultado = recomendacion_ropa(18, "lluvia ligera")
    assert "paraguas" in resultado or "impermeable" in resultado

    # Viento
    resultado = recomendacion_ropa(20, "viento fuerte")
    assert "cortavientos" in resultado


# Test de errores de API
def test_obtener_clima_error(monkeypatch):
    class MockResponseError:
        def raise_for_status(self):
            raise HTTPError("HTTP Error")

    def mock_get_error(*args, **kwargs):
        return MockResponseError()

    monkeypatch.setattr("requests.get", mock_get_error)

    resultado = obtener_clima("en Madrid")
    assert "Error de conexión" in resultado

