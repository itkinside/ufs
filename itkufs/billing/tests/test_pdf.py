from itkufs.accounting.models import Group
from itkufs.billing.models import Bill, BillingLine
from itkufs.billing.pdf import pdf


def test_bill_pdf():
    group = Group.objects.create(name="Group", slug="group")
    bill = Bill.objects.create(group=group, description="Test bill")
    BillingLine.objects.create(bill=bill, description="Line", amount=10)

    response = pdf(group, bill)

    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
