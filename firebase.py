import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
from data.models import Book, Course, PurchaseOrder, SalesInvoice, ProcessingRequest, Acquisition, InShelfAcquisition
from data import errors
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime
import logging
import sys
import os


logger = logging.getLogger()

def veriy_firebase_token(id_token:str):
    uid = None
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get('uid')
        logger.info(f'Successfully verified token for user with uid: {uid}')
    except auth.InvalidIdTokenError:
        logger.info(f'Error: Invalid ID token.')
    except ValueError:
        logger.warning(f'Error: ID token provided was not a string.')
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
    
    return uid


class Firebase:
    def __init__(self, cred_path:str='./credentials.json'):
        self.cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(self.cred)
        self.firestore = firestore.client()
    
    def get_all_data_refs(self, cls) -> list[str]:
        docs = self.firestore.collection(cls.collection_name).list_documents()
        refs = [doc_ref.id for doc_ref in docs]
        logger.info(f'Returned list of {cls.__class__} references with length: {len(refs)}')
        return refs
    
    def save_book(self, book:Book):
        doc_ref = self.firestore.collection(Book.collection_name).document(book.primary_key)
        doc_ref.set(book.to_data())
        book.primary_key = doc_ref.id
        logger.info(f'Book saved with document id: {doc_ref.id}')
        return book

    def get_book(self, isbn:str) -> Book:
        doc_ref = self.firestore.collection(Book.collection_name).document(isbn)
        data = doc_ref.get()
        if (data.exists):
            logger.info(f'Book with document id {isbn} returned.')
            return Book.from_data(isbn, data.to_dict())
        else:
            raise errors.BookNotFoundError(f'Book with accession no {isbn} not found.')
    
    def save_course(self, course:Course):
        doc_ref = self.firestore.collection(Course.collection_name).document(course.primary_key)
        doc_ref.set(course.to_data())
        course.primary_key = doc_ref.id
        logger.info(f'Course saved with document id: {doc_ref.id}')
        return course
    
    def get_course(self, course_code:str) -> Course:
        doc_ref = self.firestore.collection(Course.collection_name).document(course_code)
        data = doc_ref.get()
        if (data.exists):
            logger.info(f'Course with document id {course_code} returned.')
            return Course.from_data(course_code, data.to_dict())
        else:
            raise errors.CourseNotFoundError(f'Course with course code {course_code} not found.')
    
    def save_purchase_order(self, purchase_order:PurchaseOrder):
        doc_ref = self.firestore.collection(PurchaseOrder.collection_name).document(purchase_order.primary_key)
        doc_ref.set(purchase_order.to_data())
        purchase_order.primary_key = doc_ref.id
        logger.info(f'Purchase Order saved with document id: {doc_ref.id}')
        return purchase_order

    def get_purchase_order(self, order_no:str) -> PurchaseOrder:
        doc_ref = self.firestore.collection(PurchaseOrder.collection_name).document(order_no)
        data = doc_ref.get()
        if (data.exists):
            purchase_order_data = data.to_dict()
            purchase_order_data['order_date'] = datetime.fromisoformat(purchase_order_data['order_date'])
            logger.info(f'Purchase Order with document id {order_no} returned.')
            return PurchaseOrder.from_data(order_no, purchase_order_data)
        else:
            raise errors.PurchaseOrderNotFoundError(f'Purchase Order with order no {order_no} not found.')
    
    def save_sales_invoice(self, sales_invoice:SalesInvoice):
        doc_ref = self.firestore.collection(SalesInvoice.collection_name).document(sales_invoice.primary_key)
        doc_ref.set(sales_invoice.to_data())
        sales_invoice.primary_key = doc_ref.id
        logger.info(f'Purchase Order saved with document id: {doc_ref.id}')
        return sales_invoice
    

    def get_sales_invoice(self, invoice_no:str) -> SalesInvoice:
        doc_ref = self.firestore.collection(SalesInvoice.collection_name).document(invoice_no)
        data = doc_ref.get()
        if (data.exists):
            sales_invoice_data = data.to_dict()
            sales_invoice_data['received_on'] = datetime.fromisoformat(sales_invoice_data['received_on'])
            logger.info(f'Sales Invoice with document id {invoice_no} returned.')
            return SalesInvoice.from_data(invoice_no, sales_invoice_data)
        else:
            raise errors.SalesInvoiceNotFoundError(f'Sales Invoice with invoice no {invoice_no} not found.')

    def save_processing_request(self, processing_request:ProcessingRequest):
        doc_ref = self.firestore.collection(ProcessingRequest.collection_name).document(processing_request.primary_key)
        doc_ref.set(processing_request.to_data())
        processing_request.primary_key = doc_ref.id
        logger.info(f'Processing Request saved with document id: {doc_ref.id}')
        return processing_request

    def get_processing_request(self, request_no:str) -> ProcessingRequest:
        doc_ref = self.firestore.collection(ProcessingRequest.collection_name).document(request_no)
        data = doc_ref.get()
        if (data.exists):
            processing_request_data = data.to_dict()
            processing_request_data['request_date'] = datetime.fromisoformat(processing_request_data['request_date'])
            logger.info(f'Processing Request with document id {request_no} returned.')
            return ProcessingRequest.from_data(request_no, processing_request_data)
        else:
            raise errors.ProcessingRequestNotFoundError(f'Processing Request with request no {request_no} not found.')
    
    def save_acquisition(self, acquisition:Acquisition):
        doc_ref = self.firestore.collection(Acquisition.collection_name).document(acquisition.primary_key)
        doc_ref.set(acquisition.to_data())
        acquisition.primary_key = doc_ref.id

        logger.info(f'Acquisition saved with document id: {doc_ref.id}')
        return acquisition
    
    def get_acquisition(self, id:str) -> Acquisition:
        doc_ref = self.firestore.collection(Acquisition.collection_name).document(id)
        data = doc_ref.get()
        if (data.exists):
            acquisition_data = data.to_dict()
            acquisition_data['book'] = self.get_book(acquisition_data['isbn'])
            acquisition_data['processing_request'] = self.get_processing_request(acquisition_data['processing_request_no'])
            courses:list[Course] = [self.get_course(course_code) for course_code in acquisition_data['course_codes']]
            acquisition_data['courses'] = courses
            acquisition_data['purchase_order'] = self.get_purchase_order(acquisition_data.get('purchase_order_no'))
            acquisition_data['sales_invoice'] = self.get_sales_invoice(acquisition_data.get('sales_invoice_no'))
            logger.info(f'Processing Request with document id {id} returned.')
            return Acquisition.from_data(id, acquisition_data)
        else:
            raise errors.AcquisitionNotFoundError(f'Acquisition with id {id} not found.')
    
    def get_acquisition_by_ISBN_PR_NO(self, isbn:str, pr_no:str) -> Acquisition:
        for doc_ref in self.get_all_data_refs(Acquisition):
            doc = self.firestore.collection(Acquisition.collection_name).document(doc_ref)
            data = doc.get()
            if (data.exists):
                acquisition_data = data.to_dict()
                if (acquisition_data['isbn'] == isbn and acquisition_data['processing_request_no'] == pr_no):
                    print("Got acquisition data of the isbn and pr_no")
                    return self.get_acquisition(doc_ref)
        raise errors.AcquisitionNotFoundError(f'Acquisition with isbn: {isbn} and pr no: {pr_no} not found.')

    def save_in_shelf(self, in_shelf:InShelfAcquisition) -> InShelfAcquisition:
        doc_ref = self.firestore.collection(InShelfAcquisition.collection_name).document(in_shelf.primary_key)
        doc_ref.set(in_shelf.to_data())
        in_shelf.primary_key = doc_ref.id

        logger.info(f'In Shelf saved with document id: {doc_ref.id}')
        return in_shelf

    def get_in_shelf(self, id:str) -> InShelfAcquisition:
        doc_ref = self.firestore.collection(InShelfAcquisition.collection_name).document(id)
        data = doc_ref.get()
        if (data.exists):
            records = data.to_dict()
            return InShelfAcquisition.from_data(doc_ref.id, {'records':records})
        else:
            raise errors.InShelfAcquisitionNotFoundError(f'In Shelf with id {id} not found.')

if __name__ == '__main__':
    load_dotenv()
    firebase = Firebase('./credentials.json')
    book = Book('456', 'test1', 'john lloyd1', 'testing1', '456', '041231')
    firebase.save_book(book, "eyJhbGciOiJSUzI1NiIsImtpZCI6ImY3NThlNTYzYzBiNjRhNzVmN2UzZGFlNDk0ZDM5NTk1YzE0MGVmOTMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbGliLWFjcSIsImF1ZCI6ImxpYi1hY3EiLCJhdXRoX3RpbWUiOjE3NzAwNTgyMjgsInVzZXJfaWQiOiIzdTZtS1h2NWx0YU94aWxIbFNSZnlsZmFsVDQyIiwic3ViIjoiM3U2bUtYdjVsdGFPeGlsSGxTUmZ5bGZhbFQ0MiIsImlhdCI6MTc3MDA1ODIyOCwiZXhwIjoxNzcwMDYxODI4LCJlbWFpbCI6ImpvaG5sbG95ZHVuaWRhMEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsiam9obmxsb3lkdW5pZGEwQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.tPPGVOMXdmoW3-3Sgh7sOB_2E6X8ZDnwaPDHv6fPsQutWD9woO3A50yzOH8aSumh-F4oy1lS7iCRL3qykw6Pbl4Z82Ssq0fhYgWao-QM7ukQPmTnKZVgEKBU_-TYGtv21vgXHEISwWxw3zSeD8VGxV7x9Mg0jyY2NQJ8BrqYvIqcZHenwZFdrea42FZgLgc3PapdJDg1lFDkqoXOFqXRUWERoQhLD55RzlBk11qTSqSZjiY-csWys_0VvQzJXEX0YOtAUIN5aU00eA0bAgFNDx2mYu63OIBu2qZ7cXxsql4lmDl9sK4wA2XjIdxFKsQxoUb0BfZruqeuEkv5Z_VpcA")
    print(firebase.get_book('456').primary_key)
    print(firebase.get_all_data_refs(Book))

    course = Course('css-123', 'programming 101', 1, 'CS')
    firebase.save_course(course)
    print(firebase.get_course('css-123'))
    print(firebase.get_all_data_refs(Course))

    processing = ProcessingRequest('abc', datetime.now())
    #firebase.save_processing_request(processing)
    print(firebase.get_processing_request('abc'))
    print(firebase.get_all_data_refs(ProcessingRequest))

    #acquisition = Acquisition(None, book, processing, [course], 2019, 'testing supplier', 2019, 1, 1, 'efg', 'john lloyd', 'soit', 'hotdog', 1230.20)
    #firebase.save_acquisition(acquisition)
    print(firebase.get_all_data_refs(Acquisition))
    acquisition = firebase.get_acquisition('zRSmwnAT6QWXRjkDoE0i')
    print(acquisition.primary_key)

    purchase_order = PurchaseOrder('hijk', datetime.now())
    purchase_order = firebase.save_purchase_order(purchase_order)
    acquisition.purchase_order = purchase_order
    firebase.save_acquisition(acquisition)

    sales_invoice = SalesInvoice('123fdsaf', 'johnlloyd', datetime.now())
    sales_invoice = firebase.save_sales_invoice(sales_invoice)
    acquisition.sales_invoice = sales_invoice
    acquisition.sales_invoice_price = 1230.0
    firebase.save_acquisition(acquisition)

