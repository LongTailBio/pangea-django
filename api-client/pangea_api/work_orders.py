
from .remote_object import RemoteObject
from .blob_constructors import sample_from_uuid


class WorkOrderProto(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
    ]
    parent_field = None

    def __init__(self, knex, uuid):
        super().__init__(self)
        self.knex = knex
        self.uuid = uuid

    def get_active_work_orders(self):
        url = f'work_order_prototypes/{self.uuid}/work_orders'
        blob = self.knex.get(url)
        for wo_blob in blob['results']:
            yield WorkOrder.from_blob(self.knex, wo_blob)

    def __str__(self):
        return f'<Pangea::WorkOrderProto {self.name} {self.uuid} />'

    def __repr__(self):
        return f'<Pangea::WorkOrderProto {self.name} {self.uuid} />'

    @classmethod
    def from_uuid(cls, knex, uuid):
        obj = cls(knex, uuid)
        blob = knex.get(f'work_order_prototypes/{uuid}')
        obj.load_blob(blob)
        return obj


class WorkOrder(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'job_order_objs',
        'priority',
        'sample',
        'status',
    ]
    parent_field = None

    def __init__(self, knex, name):
        super().__init__(self)
        self.knex = knex
        self.name = name

    def get_sample(self):
        obj = sample_from_uuid(self.knex, self.sample)
        obj.url_options['work_order_uuid'] = self.uuid
        return obj

    def get_job_orders(self):
        for job_order_blob in self.job_order_objs:
            obj = JobOrder.from_blob(self, job_order_blob)
            obj._already_fetched = True
            obj._modified = False
            yield obj

    def __str__(self):
        return f'<Pangea::WorkOrder {self.name} {self.uuid} />'

    def __repr__(self):
        return f'<Pangea::WorkOrder {self.name} {self.uuid} />'

    @classmethod
    def from_blob(cls, knex, blob):
        obj = cls(knex, blob['name'])
        obj.load_blob(blob)
        return obj


class JobOrder(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'analysis_result',
        'status',
    ]
    parent_field = None

    def __init__(self, knex, work_order):
        super().__init__(self)
        self.knex = knex
        self.work_order = work_order

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        url = f'job_orders/{self.uuid}'
        self.knex.patch(url, json=data)

    def __str__(self):
        return f'<Pangea::JobOrder {self.name} {self.uuid} />'

    def __repr__(self):
        return f'<Pangea::JobOrder {self.name} {self.uuid} />'

    def pre_hash(self):
        key = self.work_order.uuid + self.name if self.name else ''
        return key

    @classmethod
    def from_blob(cls, work_order, blob):
        obj = cls(work_order.knex, work_order)
        obj.load_blob(blob)
        return obj
