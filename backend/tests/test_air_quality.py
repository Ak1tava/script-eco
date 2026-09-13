from app.services.air_quality import calculate_aqi, category_for_aqi, severity_for


def test_aqi_uses_the_worst_particulate_index() -> None:
    result = calculate_aqi(10.0, 200.0)
    assert result.value > 100
    assert result.category == "Нездоровое для чувствительных групп"


def test_high_pm25_severity() -> None:
    assert severity_for("pm25", 56) == "warning"
    assert severity_for("pm25", 80) == "high"
    assert severity_for("pm25", 110) == "critical"
    assert category_for_aqi(50) == "Хорошее"

