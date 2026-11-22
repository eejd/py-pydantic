from unittest import mock

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo


def test_model_construct_inspects_default_factory_once() -> None:
    """Repeated `model_construct` calls must not re-inspect an unchanged factory (pydantic/pydantic#14371)."""
    from pydantic._internal import _fields

    class Model(BaseModel):
        x: list[int] = Field(default_factory=list)

    with mock.patch.object(
        _fields, 'takes_validated_data_argument', wraps=_fields.takes_validated_data_argument
    ) as inspect_spy:
        for _ in range(20):
            assert Model.model_construct().x == []

    assert inspect_spy.call_count <= 1


def test_default_factory_takes_validated_data_values() -> None:
    no_arg = FieldInfo(default_factory=list)
    assert no_arg.default_factory_takes_validated_data is False

    with_data = FieldInfo(default_factory=lambda data: sorted(data))
    assert with_data.default_factory_takes_validated_data is True
    assert with_data.default_factory_takes_validated_data is True

    assert FieldInfo().default_factory_takes_validated_data is None


def test_reassigned_default_factory_recomputes_flag() -> None:
    field = FieldInfo(default_factory=list)
    assert field.default_factory_takes_validated_data is False

    field.default_factory = lambda data: sorted(data)
    assert field.default_factory_takes_validated_data is True

    field.default_factory = None
    assert field.default_factory_takes_validated_data is None


def test_copied_field_keeps_correct_flag_and_outputs() -> None:
    field = FieldInfo(default_factory=lambda data: list(data))
    assert field.default_factory_takes_validated_data is True

    copied = field._copy()
    assert copied.default_factory_takes_validated_data is True
    assert copied.get_default(call_default_factory=True, validated_data={'a': 1}) == ['a']

    copied.default_factory = list
    assert copied.default_factory_takes_validated_data is False
    assert field.default_factory_takes_validated_data is True


def test_cache_slot_not_in_repr() -> None:
    field = FieldInfo(default_factory=list)
    field.default_factory_takes_validated_data  # populate the cache
    assert '_default_factory_takes_validated_data_cache' not in repr(field)


def test_model_construct_outputs_unchanged_for_validated_data_factory() -> None:
    class Model(BaseModel):
        a: int
        b: list[int] = Field(default_factory=lambda data: [data['a']] * 2)

    assert Model.model_construct(a=3).b == [3, 3]
    assert Model.model_construct(a=4).b == [4, 4]
