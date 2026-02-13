from datetime import datetime
import json
import secrets


ATTRIBUTE_ORDER = ['processing_request', 'purchase_order', 'sales_invoice', 'delivery_receipt']


def tag_acquisition_attributes(attribute:str) -> int:
    try:
        return ATTRIBUTE_ORDER.index(attribute) + 1
    except ValueError:
        return 0


class Data:
    collection_name:str = 'datas'

    def __init__(self, primary_key:str):
        self.primary_key = primary_key
    
    def to_data(self) -> dict:
        return {}
    
    @staticmethod
    def from_data(cls, primary_key:str, data:dict) -> 'Data':
        _object = cls(primary_key)
        sorted_key_value = sorted(data.items(), key=lambda item: tag_acquisition_attributes(item[0]))
        for key, value in sorted_key_value:
            if (hasattr(_object, key)):
                setattr(_object, key, value)
        return _object


class Book(Data):
    collection_name:str = 'Book'

    def __init__(self, isbn:str, title:str=None, author:str=None, publisher:str=None, accession_no:str=None, call_number:str=None):
        super().__init__(isbn)
        self.title = title
        self.author = author
        self.publisher = publisher
        self.accession_no = accession_no
        self.call_number = call_number
    
    def to_data(self) -> dict:
        data = {
            'title':self.title, 'author':self.author, 'publisher':self.publisher, 'accession_no':self.accession_no,
            'call_number':self.call_number
        }
        return data
    
    @staticmethod
    def from_data(primary_key, data) -> 'Book':
        return Data.from_data(Book, primary_key, data)


class Course(Data):
    collection_name:str = 'Course'

    def __init__(self, course_code:str, course_title:str=None, year_level:int=None, program:str=None):
        super().__init__(course_code)
        self.course_title = course_title
        self.year_level = year_level
        self.program = program
    
    def to_data(self) -> dict:
        data = {
            'course_title':self.course_title, 'year_level':self.year_level, 'program':self.program
        }
        return data

    @staticmethod
    def from_data(primary_key, data) -> 'Course':
        return Data.from_data(Course, primary_key, data)
    

class PurchaseOrder(Data):
    collection_name:str = 'PurchaseOrder'

    def __init__(self, order_no:str, order_date:datetime=None):
        super().__init__(order_no)
        self.order_date = order_date
    
    def to_data(self) -> dict:
        data = {'order_date':self.order_date.isoformat()}
        return data
    
    @staticmethod
    def from_data(primary_key:str, data:dict) -> 'PurchaseOrder':
        if (not isinstance(data.get('order_date'), datetime)):
            raise ValueError('order_date is not of type datetime.')
        return Data.from_data(PurchaseOrder, primary_key, data)


class SalesInvoice(Data):
    collection_name:str = 'SalesInvoice'

    def __init__(self, invoice_no:str, received_by:str=None, received_on:datetime=None):
        super().__init__(invoice_no)
        self.received_by = received_by
        self.received_on = received_on
    
    def to_data(self) -> dict:
        data = {'received_by':self.received_by, 'received_on':self.received_on.isoformat()}
        return data
    
    @staticmethod
    def from_data(primary_key, data) -> 'SalesInvoice':
        if (not isinstance(data.get('received_on'), datetime)):
            raise ValueError('received_on is not of type datetime.')
        return Data.from_data(SalesInvoice, primary_key, data)


class ProcessingRequest(Data):
    collection_name:str = 'Processing'

    def __init__(self, request_no:str, request_date:datetime=None):
        super().__init__(request_no)
        self.request_date = request_date
    
    def to_data(self):
        data = {'request_date': self.request_date.isoformat()}
        return data

    @staticmethod
    def from_data(primary_key:str, data:dict) -> 'ProcessingRequest':
        if (not isinstance(data.get('request_date'), datetime)):
            raise ValueError('request_date is not of type datetime.')
        return Data.from_data(ProcessingRequest, primary_key, data)


class Acquisition(Data):
    collection_name:str = 'Acquisition'
    book:Book
    courses:list[Course]
    _purchase_order:PurchaseOrder = None
    _sales_invoice:SalesInvoice = None
    _delivery_receipt:str = None
    processing_request:ProcessingRequest = None
    stage:str = 'Waiting for PO'

    def __init__(self, id:str, book:Book=None,  processing_request:ProcessingRequest=None, courses:list[Course]=[], year_purchased:int=None, supplier:str=None, copyright:int=None, no_title:int=None, no_volumes:int=None, delivery_receipt:str=None, requestor_name:str=None, requestor_department:str=None, bundle_name:str=None, sales_invoice_price:float=None):
        if (not id):
            id = f"ACQ-{datetime.now().date().isoformat().replace('-', '')}-{secrets.token_hex(nbytes=6//2)}".upper()
        super().__init__(id)
        self.book = book
        self.processing_request = processing_request
        self.year_purchased = year_purchased
        self.supplier = supplier
        self.copyright = copyright
        self.no_title = no_title
        self.no_volumes = no_volumes
        self.delivery_receipt = delivery_receipt
        self.requestor_name = requestor_name
        self.requestor_department = requestor_department
        self.bundle_name = bundle_name
        self.sales_invoice_price = sales_invoice_price
        self.courses = courses
    
    @staticmethod
    def from_data(primary_key:str, data:dict) -> 'Acquisition':
        return Data.from_data(Acquisition, primary_key, data)
    
    def to_data(self) -> dict:
        data = {
            'isbn': self.book.primary_key, 'year_purchased':self.year_purchased, 'supplier':self.supplier,
            'copyright':self.copyright, 'no_title':self.no_title, 'no_volumes':self.no_volumes, 'delivery_receipt':self.delivery_receipt,
            'requestor_name':self.requestor_name, 'requestor_department':self.requestor_department, 'stage':self.stage, 'bundle_name':self.bundle_name,
            'processing_request_no':self.processing_request.primary_key, 'course_codes':[course.primary_key for course in self.courses],
        }
        if (self.purchase_order):
            data['purchase_order_no'] = self.purchase_order.primary_key
        if (self.sales_invoice):
            data['sales_invoice_no'] = self.sales_invoice.primary_key
            data['sales_invoice_price'] = self.sales_invoice_price
        return data
    
    def to_table(self) -> dict:
        data = {
            "PURCHASE":self.year_purchased, "SUPPLIER":self.supplier, "ACC #":self.book.accession_no,
            "CALL #":self.book.call_number, "COURSE CODE":','.join([course.primary_key for course in self.courses]), 
            "TITLE":self.book.title, "AUTHOR":self.book.author, "PUBLISHER":self.book.publisher, "COPYRIGHT":self.copyright,
             "ISBN":self.book.primary_key, "NO. OF TITLE":self.no_title, "NO. OF VOLS":self.no_volumes,
             "PROGRAM":self.courses[0].program if self.courses else "", "DR":self.delivery_receipt, "PR NO.":self.processing_request.primary_key, 
             "PR DATE":self.processing_request.request_date.isoformat(), "SI PRICE":self.sales_invoice_price, "REQUESTOR NAME":self.requestor_name,
             "REQUESTOR DEPARTMENT":self.requestor_department, "BUNDLE":self.bundle_name, "NOTES":self.stage
        }
        if (self.purchase_order):
            data['PO NO.'] = self.purchase_order.primary_key
            data['PO DATE'] = self.purchase_order.order_date.isoformat()
        if (self.sales_invoice):
            data['SI'] = self.sales_invoice.primary_key
            data['SI RECEIVED BY'] = self.sales_invoice.received_by
            data['SI RECEIVE ON'] = self.sales_invoice.received_on.isoformat()
        return data

    
    @property
    def purchase_order(self) -> PurchaseOrder:
        return self._purchase_order

    @purchase_order.setter
    def purchase_order(self, value:PurchaseOrder):
        self._purchase_order = value
        if (not self.processing_request):
            raise RuntimeError(f"No Processing Request!")
        self.stage = 'Waiting for SI'
    
    @property
    def sales_invoice(self) -> SalesInvoice:
        return self._sales_invoice

    @sales_invoice.setter
    def sales_invoice(self, value:SalesInvoice):
        self._sales_invoice = value
        if (not self.purchase_order):
            raise RuntimeError(f"No Purchase Order!")
        self.stage = 'Waiting for Delivery'
    
    @property
    def delivery_receipt(self) -> str:
        return self._delivery_receipt

    @delivery_receipt.setter
    def delivery_receipt(self, value:str):
        self._delivery_receipt = value
        self.stage = 'Done (Waiting for SI)' if (not self.sales_invoice) else 'Done'


class InShelfAcquisition(Data):
    collection_name:str = 'InShelfAcquisition'
    records:dict[str, list[(str, str, int)]]

    def __init__(self, programName:str):
        super().__init__(programName)
        self.records = {}
    
    @staticmethod
    def from_data(primary_key, data) -> 'InShelfAcquisition':
        return Data.from_data(InShelfAcquisition, primary_key, data)

    def to_data(self) -> dict:
        return self.records

    def add_acquisition(self, course_code:str, acquisition:Acquisition):
        cur_date = datetime.now().date()
        data = {"acquisition_no":acquisition.primary_key, "isbn":acquisition.book.primary_key, "copyright":acquisition.copyright}
        if (course_code in self.records):
            if (data not in self.records[course_code]):
                self.records[course_code].append(data)
        else:
            self.records[course_code] = [data]

        record = self.records[course_code]
        isbn_record = set(map(lambda item: item['isbn'], record))
        if (data['isbn'] in isbn_record):
            for i in range(len(record)-1, 0, -1):
                if (record[i]['isbn'] == data['isbn'] and record[i]['copyright'] != data['copyright'] and record[i]['copyright'] < cur_date.year - 5):
                    record.pop(i)
                    break
    


