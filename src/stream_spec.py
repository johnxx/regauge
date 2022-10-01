class StreamSpec():
    base_units = {
        'rpm': {
            'name': 'RPM',
            'suffix': '/m',
            'conversion_factor': 1
        },
        'number': {
            'name': 'number',
            'suffix': '',
            'conversion_factor': 1
        },
        'pct': {
            'name': 'percent',
            'suffix': '%',
            'conversion_factor': 1
        },
        'cel': {
            'name': 'Celcius',
            'suffix': 'c',
            'conversion_factor': 1
        },
        'lambda': {
            'name': 'lambda',
            'suffix': 'l',
            'conversion_factor': 0.0078125,
        },
        'psi': {
            'name': 'lb/in^2',
            'suffix': 'psi',
            'conversion_factor': 1
            # 'conversion_factor': 0.0625
        },
        'lpm': {
            'name': 'l/min',
            'suffix': 'lpm',
            'conversion_factor': 1
            # 'conversion_factor': 0.0625
        },
    }

    def __init__(self, field_spec, min_val=0, max_val=100, sig_digs=0, units=None) -> None:
        self.field_spec = field_spec
        self.min_val = min_val
        self.max_val = max_val
        self.sig_digs = sig_digs
        if units and isinstance(units, str):
            self.units = self.base_units[units]
        elif units and isinstance(units, dict):
            self.units = units
        else:
            unit_guess = field_spec.split('_')[-1]
            if unit_guess in self.base_units:
                self.units = self.base_units[unit_guess]
            else:
                self.units = self.base_units['number']