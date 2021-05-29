import io
import json
import time
import urllib.request
from json import JSONEncoder

import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.select import Select


class DataPoints:

    def __init__(self, eeBalance, erBalance, totalBalance, employeeShare, employerShare, pensionContributions):
        self.eeBalance = eeBalance.strip()
        self.erBalance = erBalance.strip()
        self.totalBalance = totalBalance.strip()
        self.employeeShare = employeeShare.strip()
        self.employerShare = employerShare.strip()
        self.pensionContributions = pensionContributions.strip()


class TransactionDataPoints:

    def __init__(self, transDate, finYr, particulars, dEmployeeShare, dEmployerShare, wEmployeeShare, wEmployerShare,
                 pContributions):
        self.transDate = transDate.strip()
        self.finYr = finYr.strip()
        self.particulars = particulars.strip()
        self.dEmployeeShare = dEmployeeShare.strip()
        self.dEmployerShare = dEmployerShare.strip()
        self.wEmployeeShare = wEmployeeShare.strip()
        self.wEmployerShare = wEmployerShare.strip()
        self.pContributions = pContributions.strip()


# subclass JSONEncoder
class DataPointsEncoder(JSONEncoder):

    def default(self, o):
        return o.__dict__


class UpdatedEPFOScraping:

    # init method or constructor
    def __init__(self, username, password):
        self.username = username
        self.password = password

    # For running Selenium in background
    # driver = webdriver.PhantomJS("~/phantomjs-2.1.1-macosx/bin/phantomjs")
    driver = webdriver.Chrome("~/chromedriver")
    driver.maximize_window()

    # Defining EPFO URL
    url = "https://passbook.epfindia.gov.in/MemberPassBook/Login"

    def getData(self, username, password):
        url = "https://passbook.epfindia.gov.in/MemberPassBook/Login"

        resp_dict = {}
        # loop until the control goes to the passbook page
        while url == "https://passbook.epfindia.gov.in/MemberPassBook/Login":

            res = 0

            # loop until a value is resolved from captcha
            while res == 0:

                self.driver.get(url)

                # setting username and password
                self.driver.find_element_by_name("username").send_keys(username)
                self.driver.find_element_by_name("password").send_keys(password)

                # Fetching captcha URL
                img = self.driver.find_element_by_xpath('//*[@id="captcha_id"]')
                src = img.get_attribute("src")

                # Reading image from the URL
                url_opener = urllib.request.build_opener()
                img_bytes = url_opener.open(src).read()
                img = Image.open(io.BytesIO(img_bytes))

                # Resolving Captcha
                captcha = pytesseract.image_to_string(img)

                # Removing '=' from the captcha
                captcha = captcha.replace('=', '')

                try:
                    if captcha != '':
                        res = eval(captcha)

                except:
                    res = 0

            self.driver.find_element_by_name("captcha").send_keys(res)
            button = self.driver.find_element_by_xpath('//*[@id="login"]')
            resp = button.click()
            time.sleep(2)

            url = self.driver.current_url
            if url == "https://passbook.epfindia.gov.in/MemberPassBook/Login":
                # to Add Usrname/Password validation check
                response = self.driver.find_element_by_xpath(
                    "//div[@class='alert alert-danger alert-dismissible show']/strong[1]")

                if any(i in response.text.upper() for i in ("USERNAME", "PASSWORD")):
                    resp_dict["respData"] = ""
                    resp_dict["code"] = False
                    print("Invalid Username and Passowrd, returning")
                    return

        uan = Select(self.driver.find_element_by_xpath('//*[@id="selectmid"]'))
        l = uan.options

        # Initializing Empty Dictionary
        Dict_list = []

        for x in range(1, len(l)):
            # selecting MID from dropdown
            data_dict = {}

            uan.select_by_index(x)

            # Clicking on View Passbook
            button = self.driver.find_element_by_xpath('//*[@id="btnPassbook"]')
            button.click()
            time.sleep(5)

            pagination = self.driver.find_element_by_xpath('//div[@id=\'tbl_' + l[x].text + '_paginate\']').text
            pageNos = [int(i) for i in pagination.split() if i.isdigit()]
            Trans_list = []

            # Clicking on Download Button
            button = self.driver.find_element_by_xpath('//button[@id=\'btnDownloadPassbook\']')
            button.click()
            time.sleep(5)

            # Downloading the file
            button = self.driver.find_element_by_xpath('// button[@class=\'btn btn-sm btn-success pull-right\']')
            button.click()
            time.sleep(2)

            # Closing the dialog box
            button = self.driver.find_element_by_xpath('//i[@class=\'fa fa-close\']')
            button.click()
            time.sleep(2)

            data_dict[l[x].text] = {
                'eeb': self.driver.find_element_by_xpath('//tr[1]/td[@class=\'text-bold\' and 2]').text.replace(
                    "\u20b9", "").replace(",", ""),
                'erb': self.driver.find_element_by_xpath('//tr[2]/td[@class=\'text-bold\' and 2]').text.replace(
                    "\u20b9", "").replace(",", ""),
                'tb': self.driver.find_element_by_xpath('//tr[3]/td[@class=\'text-bold\' and 2]').text.replace("\u20b9",
                                                                                                               "").replace(
                    ",", ""),
                # 'dep_eps': self.driver.find_element_by_xpath('//tfoot/tr[1]/td[2]').text.replace(",", ""),
                # 'dep_ers': self.driver.find_element_by_xpath('//tfoot/tr[1]/td[3]').text.replace(",", ""),
                # 'wit_eps': self.driver.find_element_by_xpath('//tfoot/tr[1]/td[4]').text.replace(",", ""),
                # 'wit_ers': self.driver.find_element_by_xpath('//tfoot/tr[1]/td[5]').text.replace(",", ""),
                # 'pc': self.driver.find_element_by_xpath('//tfoot/tr[1]/td[6]').text.replace(",", ""),

            }

            for pn in range(0, len(pageNos)):
                button = self.driver.find_element_by_xpath('//li[' + str(pn + 2) + ']/a[1]')
                button.click()
                for row in range(1, 11):
                    try:
                        eachTransaction = {
                            'tD': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[1]').text,
                            'fY': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[2]').text,
                            'par': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[3]').text,
                            'dEPS': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[4]').text,
                            'dERS': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[5]').text,
                            'wEPS': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[6]').text,
                            'wERS': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[7]').text,
                            'pContri': self.driver.find_element_by_xpath(
                                '// table[@id=\'tbl_' + l[x].text + '\']/tbody[1]/tr[' + str(row) + ']/td[8]').text,
                        }
                    except:
                        break

                    Trans_list.append(eachTransaction)

                time.sleep(3)

            data_dict[l[x].text]["transactions"] = Trans_list

            Dict_list.append(data_dict)

            f = open("/Users/admin/Downloads/" + l[x].text + ".pdf", "w+")
            print(f)

        # data_dict['eeb'] = self.driver.find_element_by_xpath('//tr[1]/td[@class=\'text-bold\' and 2]').text.replace("\u20b9", "").replace(",", "")
        # data_dict['erb'] = self.driver.find_element_by_xpath('//tr[2]/td[@class=\'text-bold\' and 2]').text.replace("\u20b9", "").replace(",", "")
        # data_dict['tb'] = self.driver.find_element_by_xpath('//tr[3]/td[@class=\'text-bold\' and 2]').text.replace("\u20b9", "").replace(",", "")
        # data_dict['dep_eps'] = self.driver.find_element_by_xpath('//tfoot/tr[1]/td[2]').text.replace(",", "")
        # data_dict['dep_ers'] = self.driver.find_element_by_xpath('//tfoot/tr[1]/td[3]').text.replace(",", "")
        # data_dict['wit_eps'] = self.driver.find_element_by_xpath('//tfoot/tr[1]/td[4]').text.replace(",", "")
        # data_dict['wit_ers'] = self.driver.find_element_by_xpath('//tfoot/tr[1]/td[5]').text.replace(",", "")
        # data_dict['pc'] = self.driver.find_element_by_xpath('//tfoot/tr[1]/td[6]').text.replace(",", "")

        # Creating datapoints object
        # dataPoint = DataPoints(eeb.text, erb.text, tb.text, eps.text, ers.text, pc.text)

        # Adding datapoints to dictionary
        # Dict[l[x].text] = DataPointsEncoder().encode(dataPoint)

        print(json.dumps(Dict_list))

        resp_dict["respData"] = json.dumps(Dict_list)
        resp_dict["code"] = True
        print("Done all")


epfoScraping = UpdatedEPFOScraping("XXXXXXXXX", "XXXXXXXXX")
epfoScraping.getData("XXXXXXXXX", "XXXXXXXXX")
