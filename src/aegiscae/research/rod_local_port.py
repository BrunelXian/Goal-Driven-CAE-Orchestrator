"""Pinned original AF public reader; no arbitrary result provider product input.

This is an application boundary, not a Python sandbox against same-user mutation.
No process start, Project creation or authority API is exposed.
"""
import copy

from aegiscae.contracts.research_contracts import require


class LocalReadPort:
    def __init__(self, af_project, config, runtime):
        from abqjobpilot.product_rod import RodProduct
        self._product = RodProduct(af_project)
        self._config = config
        self._runtime = copy.deepcopy(runtime)
        self.validate(runtime)

    def validate(self, runtime):
        from abqjobpilot.product_rod import validate_local_reader
        require(self._runtime == runtime, 'READ_PORT_UNQUALIFIED')
        validate_local_reader(self._product, self._config, runtime)

    def preflight_real(self, **refs):
        return self._product.preflight_real(config=self._config, **refs)

    def read_acceptance(self, **refs):
        return self._product.read_acceptance(**refs)

    def read_started(self, **refs):
        return self._product.read_started(**refs)

    def read_denial(self, **refs):
        return self._product.read_denial(**refs)

    def read_real_artifacts(self, **refs):
        return self._product.read_real_artifacts(**refs)

    def read_orderly_stop(self, **refs):
        return self._product.read_orderly_stop(**refs)
