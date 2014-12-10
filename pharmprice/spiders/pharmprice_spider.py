# -*- coding: utf-8 -*-
__author__ = 'kuanysh'

import sys
import scrapy
from pharmprice.items import PharmpriceItem
from scrapy.utils.response import open_in_browser
from scrapy.http import Request
from scrapy.selector import Selector
import urlparse
import re
import urllib2
import numpy

class PharmpriceSpider(scrapy.Spider):
    name = "pharmprice"
    allowed_domains = ["pharmprice.kz"]
    start_urls = [
            "http://www.pharmprice.kz/annotations.php?KeyIndex=A"
            ]
    download_delay = 0.3

    def parse(self, response):
        #yield Request("http://www.pharmprice.kz/annotation.php?id=8377", self.parseAnnotation)

        # handle links to letters
        crawledLinks = []
        letLinks = response.xpath('//a[contains(@href, "annotations.php?KeyIndex=")]/@href').extract()

        #print("total letter links" + str(len(letLinks)))

        for letIndex in range(1, len(letLinks)):
            #cur_link = urlparse.urljoin(response.url, letLinks[letIndex].strip())
            cur_link = letLinks[letIndex].strip()

            # check and handle russian letter
            curLetter = cur_link[-1]
            if ord(curLetter)>=1040:
                linkDict = ['%C0', '%C1', '%C2', '%C3', '%C4', '%C5', '%C6', '%C7', '%C8', '%C9', '%CA', '%CB',
                            '%CC', '%CD', '%CE', '%CF', '%D0', '%D1', '%D2', '%D3', '%D4', '%D5', '%D6','%D7',
                            '%D8', '%D9','%DA', '%DB', '%DC','%DD', '%DE', '%DF']
                cur_link = cur_link[:-1] + linkDict[ord(curLetter)-1040]

            cur_link = "http://www.pharmprice.kz/" + cur_link
            #print("current link " + cur_link)

            if not cur_link in crawledLinks:
                #cur_link  = re.sub('[0%A]', '', cur_link)
                crawledLinks.append(cur_link )
                yield Request(cur_link , self.parse2)

    def parse2(self, response):
        rows = response.xpath('//table[@class="table table-bordered"]/descendant::tr')

        for rownum in range(1, len(rows)):
            item = PharmpriceItem()
            drugLink = ''.join(rows[rownum].xpath("td[1]/a/@href").extract())
            drugLink = urlparse.urljoin(response.url, drugLink .strip())
            item['link'] = drugLink
            item['tradeName'] = ''.join(rows[rownum].xpath("td[1]/a/text()").extract())
            item['regNumber'] = ''.join(rows[rownum].xpath("td[2]/a/text()").extract())

            MNN = re.sub('[\n\t\r]', '', ''.join(rows[rownum].xpath("td[3]/a/text()").extract()))
            item['MNN'] = MNN.strip()

            item['manufacturer'] = ''.join(rows[rownum].xpath("td[4]/a/text()").extract())

            groupATH = re.sub('[\n\t\r]', '',''.join(rows[rownum].xpath("td[5]/a/text()").extract()))
            item['groupATH'] = groupATH.strip()

            yield Request(drugLink, self.parseAnnotation, meta={'item':item})

        # when done with this page handle next pages if available
        nextPageLink  = ''.join(response.xpath('//ul[@class="pagination"]/descendant::li[@class="active"]/following::li[1]/a/@href').extract())
        nextPageText = ''.join(response.xpath('//ul[@class="pagination"]/descendant::li[@class="active"]/following::li[1]/a/text()').extract())

        if nextPageLink and nextPageText.isdigit():
            # check for russian letters
            curLetter = nextPageLink[-1]
            if ord(curLetter)>=1040:
                linkDict = ['%C0', '%C1', '%C2', '%C3', '%C4', '%C5', '%C6', '%C7', '%C8', '%C9', '%CA', '%CB',
                            '%CC', '%CD', '%CE', '%CF', '%D0', '%D1', '%D2', '%D3', '%D4', '%D5', '%D6','%D7',
                            '%D8', '%D9','%DA', '%DB', '%DC','%DD', '%DE', '%DF']
                nextPageLink = nextPageLink[:-1] + linkDict[ord(curLetter)-1040]

            nextPageLink = urlparse.urljoin(response.url, nextPageLink.strip())
            yield Request(nextPageLink, self.parse2)

    def parseAnnotation(self, response):
            item = response.meta['item']

            responseText = ''.join(response.xpath("//body/descendant::node()/text()").extract())
            #print(responseText)

            keyWords = [u'Адрес организации, принимающей на территории Республики Казахстан претензии потребителей по качеству продукции',
                        u'Владелец регистрационного удостоверения', u'Владелец регистрационногоудостоверения',
                        u'Владелецрегистрационного удостоверения', u'Владелецрегистрационногоудостоверения',
                        u'Лекарственная форма', u'Лекарственнаяформа',
                        u'Лекарственные взаимодействия',u'Лекарственныевзаимодействия',
                        u'Международное непатентованное название', u'Международноенепатентованное название',
                        u'Международноенепатентованное название', u'Международноенепатентованноеназвание',
                        u'Несовместимость', u'Описание', u'Особые указания', u'Особыеуказания',u'Передозировка',
                        u'Побочные действия',u'Побочныедействия',u'Показания к применению', u'Показания кприменению',
                        u'Показанияк применению',u'Показаниякприменению',u'Применение в педиатрии',
                        u'Производитель', u'Противопоказания',u'Состав',u'Способ применения и дозы',
                        u'Срок хранения', u'Срокхранения',u'Торговое название',u'Торговоеназвание',
                        u'Упаковщик', u'Условия отпуска', u'Условияотпуска', u'Условия хранения', u'Условияхранения',
                        u'Фармакодинамика', u'Фармакокинетика',
                        u'Фармакологические свойства',u'Фармакологическиесвойства',
                        u'Фармакотерапевтическая группа',u'Фармакотерапевтическаягруппа',
                        u'Форма выпуска и упаковка', u'Форма выпуска иупаковка',u'Форма выпускаиупаковка',
                        u'Формавыпускаиупаковка', u'Формавыпуска иупаковка', u'Формавыпуска и упаковка']

            # go through keywords
            kwPositions = []

            for keyWord in keyWords:
                kwSP = responseText.find(keyWord) #keyword start position
                if kwSP !=-1:
                    #print(keyWord + ": " + str(kwSP))
                    kwPositions.append(kwSP)

            #print(kwPositions)
            kwArray = numpy.array(kwPositions)

            # extract drugGenericName
            curKw = u"Международное непатентованное название"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugGenericName = responseText[(curSP + len(curKw)):nextSection]
                item['drugGenericName'] = re.sub('[\n\t\r]', ' ', drugGenericName.strip())

            # extract drugForm
            curKw = u"Лекарственная форма"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugForm = responseText[(curSP + len(curKw)):nextSection]
                item['drugForm'] = re.sub('[\n\t\r]', ' ', drugForm.strip())


            # extract drugContent
            curKw = u"Состав"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugContent = responseText[(curSP + len(curKw)):nextSection]
                item['drugContent'] = re.sub('[\n\t\r]', ' ', drugContent.strip())

            # extract drugProperties
            curKw = u"Фармакодинамика"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugProperties = responseText[(curSP + len(curKw)):nextSection]
                item['drugProperties'] = re.sub('[\n\t\r]', ' ', drugProperties.strip())

            # extract drugIndication
            curKw = u"Показания к применению"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugIndication = responseText[(curSP + len(curKw)):nextSection]
                item['drugIndication'] = re.sub('[\n\t\r]', ' ', drugIndication.strip())

            # extract drugDosage
            curKw = u"Способ применения и дозы"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugDosage = responseText[(curSP + len(curKw)):nextSection]
                item['drugDosage'] = re.sub('[\n\t\r]', ' ', drugDosage.strip())

            # extract drugSide
            curKw = u"Побочные действия"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugSide = responseText[(curSP + len(curKw)):nextSection]
                item['drugSide'] = re.sub('[\n\t\r]', ' ', drugSide.strip())

            # extract drugContrIndication
            curKw = u"Противопоказания"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugContrIndication = responseText[(curSP + len(curKw)):nextSection]
                item['drugContrIndication'] = re.sub('[\n\t\r]', ' ', drugContrIndication.strip())

            # extract drugInteractions
            curKw = u"Лекарственные взаимодействия"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugInteractions = responseText[(curSP + len(curKw)):nextSection]
                item['drugInteractions'] = re.sub('[\n\t\r]', ' ', drugInteractions.strip())

            # extract drugSpecial
            curKw = u"Особые указания"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugSpecial = responseText[(curSP + len(curKw)):nextSection]
                item['drugSpecial'] = re.sub('[\n\t\r]', ' ', drugSpecial.strip())

            # extract drugExpiry
            curKw = u"Срок хранения"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugExpiry = responseText[(curSP + len(curKw)):nextSection]
                item['drugExpiry'] = re.sub('[\n\t\r]', ' ', drugExpiry.strip())

            # extract drugRetailCondition
            curKw = u"Условия отпуска из аптек"
            curSP = responseText.find(curKw)
            if curSP != -1:
                if len(kwArray[kwArray>curSP])>0:
                    nextSection = min(kwArray[kwArray>curSP])
                else:
                    nextSection = len(responseText)

                drugRetailCondition = responseText[(curSP + len(curKw)):nextSection]
                item['drugRetailCondition'] = re.sub('[\n\t\r]', ' ', drugRetailCondition.strip())

            """
            - Название
            - Синонимы (для подбора схожих лекарств)
            - лекарственная форма
            - состав
            - Фармакодинамика (или "свойства" иногда называется "описание")
            - Показания к применению
            - Способ применения и дозы
            - Побочное действие
            - Противопоказания
            - Лекарственные взаимодействия
            - Особые указания
            - срок хранения
            - условия отпуска из аптеки
            """

            return item