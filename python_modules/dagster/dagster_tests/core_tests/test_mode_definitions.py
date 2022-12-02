import pytest

from dagster import DagsterInvalidDefinitionError, DagsterInvariantViolationError, resource
from dagster._check import CheckError
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._legacy import ModeDefinition, execute_pipeline, pipeline, solid
from dagster._utils.test import execute_solids_within_pipeline


def define_single_mode_pipeline():
    @solid
    def return_two(_context):
        return 2

    return JobDefinition(
        graph_def=GraphDefinition(
            name="single_mode",
            node_defs=[return_two],
        ),
        _mode_def=ModeDefinition(name="the_mode"),
    )


def test_default_mode_definition():
    pipeline_def = JobDefinition(graph_def=GraphDefinition(name="takesamode", node_defs=[]))
    assert pipeline_def


def test_mode_takes_a_name():
    pipeline_def = JobDefinition(
        graph_def=GraphDefinition(
            name="takesamode",
            node_defs=[],
        ),
        _mode_def=ModeDefinition(name="a_mode"),
    )
    assert pipeline_def


def test_error_on_invalid_resource_key():
    @resource
    def test_resource():
        return ""

    with pytest.raises(CheckError, match="test-foo"):
        ModeDefinition(
            resource_defs={
                "test-foo": test_resource,
            },
        )


def test_mode_from_resources():
    @solid(required_resource_keys={"three"})
    def ret_three(context):
        return context.resources.three

    @pipeline(
        name="takesamode",
        mode_defs=[ModeDefinition.from_resources({"three": 3}, name="three")],
    )
    def pipeline_def():
        ret_three()

    assert execute_pipeline(pipeline_def).result_for_node("ret_three").output_value() == 3


def test_execute_single_mode():
    single_mode_pipeline = define_single_mode_pipeline()
    assert single_mode_pipeline.is_single_mode is True

    assert execute_pipeline(single_mode_pipeline).result_for_node("return_two").output_value() == 2

    assert (
        execute_pipeline(single_mode_pipeline, mode="the_mode")
        .result_for_node("return_two")
        .output_value()
        == 2
    )


def test_wrong_single_mode():
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            execute_pipeline(pipeline=define_single_mode_pipeline(), mode="wrong_mode")
            .result_for_node("return_two")
            .output_value()
            == 2
        )


<<<<<<< HEAD
def test_mode_double_default_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        JobDefinition(
            name="double_default",
            solid_defs=[],
            mode_defs=[ModeDefinition(), ModeDefinition()],
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "default" in "double_default". '
        "Modes must have unique names."
    )


def test_mode_double_given_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        JobDefinition(
            name="double_given",
            solid_defs=[],
            mode_defs=[ModeDefinition(name="given"), ModeDefinition(name="given")],
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "given" in "double_given". '
        "Modes must have unique names."
    )


def test_execute_multi_mode():
    multi_mode_pipeline = define_multi_mode_pipeline()

    assert (
        execute_pipeline(pipeline=multi_mode_pipeline, mode="mode_one")
        .result_for_node("return_three")
        .output_value()
        == 3
    )

    assert (
        execute_pipeline(pipeline=multi_mode_pipeline, mode="mode_two")
        .result_for_node("return_three")
        .output_value()
        == 3
    )


def test_execute_multi_mode_errors():
    multi_mode_pipeline = define_multi_mode_pipeline()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline)

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline=multi_mode_pipeline, mode="wrong_mode")


def test_execute_multi_mode_with_resources():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    add_mode_result = execute_pipeline(
        pipeline=pipeline_def,
        mode="add_mode",
        run_config={"resources": {"op": {"config": 2}}},
    )

    assert add_mode_result.result_for_node("apply_to_three").output_value() == 5

    mult_mode_result = execute_pipeline(
        pipeline=pipeline_def,
        mode="mult_mode",
        run_config={"resources": {"op": {"config": 3}}},
    )

    assert mult_mode_result.result_for_node("apply_to_three").output_value() == 9


=======
>>>>>>> 15470d3713 (update PipelineDefinition invocations)
def test_mode_with_resource_deps():

    called = {"count": 0}

    @resource
    def resource_a():
        return 1

    @solid(required_resource_keys={"a"})
    def requires_a(context):
        called["count"] += 1
        assert context.resources.a == 1

    pipeline_def_good_deps = JobDefinition(
        graph_def=GraphDefinition(
            name="mode_with_good_deps",
            node_defs=[requires_a],
        ),
        _mode_def=ModeDefinition(resource_defs={"a": resource_a}),
    )

    execute_pipeline(pipeline_def_good_deps)

    assert called["count"] == 1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'a' required by op 'requires_a' was not provided",
    ):
        JobDefinition(
            graph_def=GraphDefinition(
                name="mode_with_bad_deps",
                node_defs=[requires_a],
            ),
            _mode_def=ModeDefinition(resource_defs={"ab": resource_a}),
        )

    @solid(required_resource_keys={"a"})
    def no_deps(context):
        called["count"] += 1
        assert context.resources.a == 1

    pipeline_def_no_deps = JobDefinition(
        graph_def=GraphDefinition(
            name="mode_with_no_deps",
            node_defs=[no_deps],
        ),
        _mode_def=ModeDefinition(resource_defs={"a": resource_a}),
    )

    execute_pipeline(pipeline_def_no_deps)

    assert called["count"] == 2


def test_subset_with_mode_definitions():

    called = {"a": 0, "b": 0}

    @resource
    def resource_a():
        return 1

    @solid(required_resource_keys={"a"})
    def requires_a(context):
        called["a"] += 1
        assert context.resources.a == 1

    @resource
    def resource_b():
        return 2

    @solid(required_resource_keys={"b"})
    def requires_b(context):
        called["b"] += 1
        assert context.resources.b == 2

    pipeline_def = JobDefinition(
        graph_def=GraphDefinition(
            name="subset_test",
            node_defs=[requires_a, requires_b],
        ),
        _mode_def=ModeDefinition(resource_defs={"a": resource_a, "b": resource_b}),
    )

    assert execute_pipeline(pipeline_def).success is True

    assert called == {"a": 1, "b": 1}

    assert (
        execute_solids_within_pipeline(pipeline_def, solid_names={"requires_a"})[
            "requires_a"
        ].success
        is True
    )

    assert called == {"a": 2, "b": 1}


def parse_captured_results(captured_results):
    # each result will be a tuple like:
    # (10,
    # 'multi_mode - 1cc8958b-5ce6-401a-9e2a-ddd653e59a7e - PIPELINE_START - Started execution of '
    # 'pipeline "multi_mode".'
    # )
    # so, this will reconstruct the original message from the captured log line.

    # Extract the text string and remove key = value tuples on later lines
    return [x[1].split("\n")[0] for x in captured_results]
