from marshmallow import Serializer, fields


class CustomerAddress(Serializer):
    city = fields.String()
    cityCode = fields.String()
    countryCode = fields.String()
    street = fields.String()
    postalCode = fields.String()


class Customer(Serializer):
    customerId = fields.UUID()
    address = fields.Nested(CustomerAddress)


class Device(Serializer):
    dateStart = fields.DateTime(format='iso')
    dateEnd = fields.DateTime(format='iso')
    deviceId = fields.UUID()


class Contract(Serializer):
    companyId = fields.Integer()
    ownerId = fields.UUID()
    payerId = fields.UUID()
    dateStart = fields.DateTime(format='iso')
    dateEnd = fields.DateTime(format='iso')
    contractId = fields.String()
    tariffId = fields.String()
    power = fields.Integer()
    version = fields.Integer()
    activityCode = fields.String()
    meteringPointId = fields.UUID()
    customer = fields.Nested(Customer)
    devices = fields.List(fields.Nested(Device))