import os
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import NumberParseException
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer



def check_number(number):
    try:
        country_format = phonenumbers.format_number(
            phonenumbers.parse(number, "NG"),
            phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        )
    except NumberParseException:
        raise ValueError("String supplied as number did not seem to be a phone number ")
    number_profile = phonenumbers.parse(country_format, "NG")
    telco = repr(carrier.name_for_number(number_profile, "en"))

    response = telco.strip("'") or False
    if response:
        return country_format.replace(" ", "")
    else:
        return False


def format_number_properly(value):
    if value[0] == "+":
        if value[0:4] == "+234":
            return value
        else:
            # Nullify value. Nigeria Alone
            # return None
            return "0000"
    elif value[0:3] == "234":
        return "+" + value
    elif value[0] == "0":
        return "+234" + value[1:]
    else:
        # Nullify value. Nigeria Alone
        # return None
        # return value
        return "0000"




def get_bank_name(bank_code):
    if bank_code == "044":
        return "Access Bank"
    elif bank_code == "063":
        return "Access Bank Diamond"
    elif bank_code == "035A":
        return "ALAT by WEMA"
    elif bank_code == "401":
        return "ASO Savings and Loans"
    elif bank_code == "50823":
        return "CEMCS Microfinance Bank"
    elif bank_code == "023":
        return "Citibank Nigeria"
    elif bank_code == "050":
        return "Ecobank Nigeria"
    elif bank_code == "562":
        return "Ekondo MicroFinance Bank"
    elif bank_code == "070":
        return "Fidelity Bank"
    elif bank_code == "011":
        return "First Bank of Nigeria"
    elif bank_code == "214":
        return "First City Monument Bank"
    elif bank_code == "00103":
        return "Globus Bank"
    elif bank_code == "058":
        return "Guaranty Trust Bank"
    elif bank_code == "50383":
        return "Hasal Microfinance Bank"
    elif bank_code == "030":
        return "Heritage Bank"
    elif bank_code == "301":
        return "Jaiz Bank"
    elif bank_code == "082":
        return "Keystone Bank"
    elif bank_code == "50211":
        return "Kuda Bank"
    elif bank_code == "526":
        return "Parallex Bank"
    elif bank_code == "076":
        return "Polaris Bank"
    elif bank_code == "101":
        return "Providus Bank"
    elif bank_code == "125":
        return "Rubies MFB"
    elif bank_code == "51310":
        return "Sparkle Microfinance Bank"
    elif bank_code == "221":
        return "Stanbic IBTC Bank"
    elif bank_code == "232":
        return "Sterling Bank"
    elif bank_code == "100":
        return "Suntrust Bank"
    elif bank_code == "302":
        return "TAJ Bank"
    elif bank_code == "51211":
        return "TCF MFB"
    elif bank_code == "102":
        return "Titan Bank"
    elif bank_code == "032":
        return "Union Bank of Nigeria"
    elif bank_code == "033":
        return "United Bank For Africa"
    elif bank_code == "215":
        return "Unity Bank"
    elif bank_code == "566":
        return "VFD"
    elif bank_code == "035":
        return "Wema Bank"
    elif bank_code == "057":
        return "Zenith Bank"



def get_cosine_similarity(vectorA, vectorB):
    """
    A measure of similarity between two non-zero vectors of an inner product 
    space that measures the cosine of the angle between them.
    """
    array = [vectorA.lower(), vectorB.lower()]
    vectorizer = CountVectorizer().fit_transform(array)
    vectors =  vectorizer.toarray()

    vecA = vectors[0].reshape(1, -1)
    vecB = vectors[1].reshape(1, -1)

    return cosine_similarity(vecA, vecB)[0][0]