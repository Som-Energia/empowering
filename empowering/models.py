from marshmallow import Schema, fields, post_dump
from marshmallow.validate import OneOf

def remove_none(struct):
    converted = struct.copy()
    for key, value in struct.items():
        if isinstance(value, dict):
            converted[key] = remove_none(value)
        else:
            if (value is None or (isinstance(value, bool) and not value)): 
                del converted[key]
    return converted

class BaseSchema(Schema):
    @post_dump
    def remove_none(self, data):
        return remove_none(data)

class Integer(fields.Integer):
    def __init__(self, default=None, **kwargs):
        super(Integer, self).__init__(default=default, **kwargs)


class StringDateTime(fields.DateTime):
    def _serialize(self, value, attr, obj):
        if isinstance(value, basestring):
            return value
        else:
            return super(StringDateTime, self)._serialize(value, attr, obj)


class CustomerAddress(BaseSchema):
    buildingId = fields.UUID()
    country = fields.String()
    countryCode = fields.String()
    province = fields.String()
    provinceCode = fields.String()
    city = fields.String()
    cityCode = fields.String()
    street = fields.String()
    postalCode = fields.String()
    parcelNumber = fields.String()


class CustomerBuildingData(BaseSchema):
    buildingConstructionYear = Integer()
    dwellingArea = Integer()
    buildingVolume = Integer()
    buildingType = fields.Str(validate=OneOf(['Single_house', 'Apartment']))
    dwellingPositionInBuilding = fields.Str(validate=OneOf([
        'first_floor', 'middle_floor', 'last_floor', 'other'
    ]))
    dwellingOrientation = fields.Str(validate=OneOf([
        'S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW'
    ]))
    buildingWindowsType = fields.Str(validate=OneOf([
        'single_panel', 'double_panel', 'triple_panel', 'low_emittance', 'other'
    ]))
    buildingWindowsFrame = fields.Str(validate=OneOf([
        'PVC', 'wood', 'aluminium', 'steel', 'other'
    ]))
    buildingHeatingSource = fields.Str(validate=OneOf([
        'electricity', 'gas', 'gasoil', 'district_heating', 'biomass', 'other'
    ]))
    buildingHeatingSourceDhw = fields.Str(validate=OneOf([
        'electricity', 'gas', 'gasoil', 'district_heating', 'biomass', 'other'
    ]))
    buildingSolarSystem = fields.Str(validate=OneOf([
        'PV', 'solar_thermal_heating', 'solar_thermal_DHW', 'other',
        'not_installed'
    ]))


class CustomerProfileEducationLevel(BaseSchema):
    edu_prim = Integer()
    edu_sec = Integer()
    edu_uni = Integer()
    edu_noStudies = Integer()


class CustomerProfile(BaseSchema):
    totalPersonNumber = Integer()
    minorsPersonsNumber = Integer()
    workingAgePersonsNumber = Integer()
    retiredAgePersonsNumber = Integer()
    malePersonsNumber = Integer()
    femalePersonsNumber = Integer()
    educationLevel = fields.Nested(CustomerProfileEducationLevel)

class CustomerCustomisedGroupingCriteria(BaseSchema):
    pass


class CustomerCustomisedServiceParameters(BaseSchema):
    OT101 = fields.String()
    OT103 = fields.String()
    OT105 = fields.String()
    OT106 = fields.String()
    OT109 = fields.String()
    OT201 = fields.String()
    OT204 = fields.String()
    OT401 = fields.String()
    OT502 = fields.String()
    OT503 = fields.String()
    OT603 = fields.String()
    OT603g = fields.String()
    OT701 = fields.String()
    OT703 = fields.String()


class Customer(BaseSchema):
    customerId = fields.UUID()
    address = fields.Nested(CustomerAddress)
    buildingData = fields.Nested(CustomerBuildingData)
    profile = fields.Nested(CustomerProfile)
    customisedGroupingCriteria = fields.Nested(
        CustomerCustomisedGroupingCriteria
    )
    customisedServiceParameters = fields.Nested(
        CustomerCustomisedServiceParameters
    )

class Device(BaseSchema):
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    deviceId = fields.UUID()

class Tariff(BaseSchema):
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    tariffId = fields.String()

class TariffHistory(BaseSchema):
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    tariffId = fields.String()

class Power(BaseSchema):
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    power = Integer() 
 
class PowerHistory(BaseSchema):
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    power = Integer() 

class Contract(BaseSchema):
    payerId = fields.UUID()
    ownerId = fields.UUID()
    signerId = fields.UUID()
    power = Integer()
    power_ = fields.Nested(Power)
    powerHistory = fields.List(fields.Nested(PowerHistory))
    dateStart = StringDateTime(format='iso')
    dateEnd = StringDateTime(format='iso')
    contractId = fields.String()
    tariffId = fields.String()
    tariff_ = fields.Nested(Tariff)
    tariffHistory = fields.List(fields.Nested(TariffHistory))
    version = Integer()
    activityCode = fields.String()
    meteringPointId = fields.UUID()
    climiaticZone = fields.String()
    weatherStationId = fields.UUID()
    experimentalGroupUser = fields.Boolean()
    experimentalGroupUserTest = fields.Boolean()
    activeUser = fields.Boolean()
    activeUserDate = StringDateTime(format='iso')
    customer = fields.Nested(Customer)
    devices = fields.List(fields.Nested(Device))


class Reading(BaseSchema):
    type = fields.Str(validate=OneOf([
        'electricityConsumption', 'electricityKiloVoltAmpHours',
        'heatConsumption', 'gasConsumption', 'estimatedElectricityConsumption',
        'estimatedElectricityKiloVoltAmpHours', 'estimatedHeatConsumption',
        'estimatedGasConsumption'
    ]))
    unit = fields.Str(validate=OneOf(['kWh', 'Wh']))
    period = fields.Str(validate=OneOf(['INSTANT', 'CUMULATIVE', 'PULSE']))


class Measurement(BaseSchema):
    type = fields.Str(validate=OneOf(['electricityConsumption']))
    timestamp = StringDateTime(format='iso')
    value = fields.Float()


class AmonMeasure(BaseSchema):
    deviceId = fields.UUID()
    meteringPointId = fields.UUID()
    readings = fields.List(fields.Nested(Reading))
    measurements = fields.List(fields.Nested(Measurement))
