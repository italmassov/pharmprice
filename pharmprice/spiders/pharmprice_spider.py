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

class PharmpriceSpider(scrapy.Spider):
    name = "pharmprice"
    allowed_domains = ["pharmprice.kz"]
    start_urls = [
            "http://www.pharmprice.kz/annotations.php?KeyIndex=A"
            ]
    download_delay = 0.3

    def parse(self, response):
        # handle links to letters
        crawledLinks = []
        letLinks = response.xpath('//a[contains(@href, "annotations.php?KeyIndex=")]/@href').extract()

        #print("total letter links" + str(len(letLinks)))

        for letIndex in range(27, len(letLinks)):
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
        #print("number of rows" + str(len(rows)))

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

    def parseAnnotation(self, response):
            item = response.meta['item']

            enhResponse = ''.join(response.xpath("//body").extract())
            #print(enhResponse)
            responseText = ''.join(response.xpath("//body/text()").extract())

            keyWords = [u'Адрес организации, принимающей на территории Республики Казахстан претензии потребителей по качеству продукции',
                        u'Владелец регистрационного удостоверения', u'Владелец регистрационногоудостоверения',
                        u'Владелецрегистрационного удостоверения', u'Владелецрегистрационногоудостоверения'
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
            for keyWord in keyWords:
                searchKW =  '<p class="MsoNormal">' + keyWord   #search keyword
                kwSP = enhResponse.find(searchKW) #keyword start position

                if kwSP ==-1:
                    searchKW =  '<p class="MsoNormal">\n"' + keyWord  #search keyword
                    kwSP = enhResponse.find(searchKW) #keyword start position

                if kwSP ==-1:
                    searchKW =  '<p>' + keyWord   #search keyword
                    kwSP = enhResponse.find(searchKW) #keyword start position

                #replacing style for appropriate
                if kwSP != -1:
                    classSP = enhResponse.find("MsoNormal",kwSP+1)
                    if classSP != -1:
                        classEP = classSP + len("MsoNormal")
                        enhResponse =  enhResponse[:classSP] + "section" + enhResponse[classEP:]

            #extract keywords
            enhSelector = Selector(text=enhResponse)

            # extract word 1
            folClasses =  enhSelector.xpath("//p[contains(text(),'%s')]/following::p/@class" % u"Международное непатентованное название").extract()
            if folClasses:
                folSectPos = str(folClasses.index(u"section")+1)
                xpathSynt = "//p[contains(text(),'%s')]/following::p[position()<=" + folSectPos + "]/text()"
                drugGenericName = ''.join(enhSelector.xpath(xpathSynt % u"Международное непатентованное название").extract())
                item['drugGenericName'] = re.sub('[\n\t\r]', '', drugGenericName.strip())

            # extract word 2
            folClasses =  enhSelector.xpath("//p[contains(text(),'%s')]/following::p/@class" % u"Лекарственная форма").extract()
            if folClasses:
                folSectPos = str(folClasses.index(u"section")+1)
                xpathSynt = "//p[contains(text(),'%s')]/following::p[position()<=" + folSectPos + "]/text()"
                drugForm = ''.join(enhSelector.xpath(xpathSynt % u"Лекарственная форма").extract())
                item['drugForm'] = re.sub('[\n\t\r]', '', drugForm .strip())


            """
            drugForm = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Лекарственная форма").extract())
            drugContent = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Cостав").extract())
            drugProperties = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Фармакодинамика").extract())
            drugIndication = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Показания к применению").extract())
            drugDosage = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Способ применения и дозы").extract())
            drugSide = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Побочные действия").extract())
            drugContrIndication = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Противопоказания").extract())
            drugInteractions = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Лекарственные взаимодействия").extract())
            drugSpecial = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Особые указания").extract())
            drugExpiry = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Срок хранения").extract())
            drugRetailCondition = ''.join(response.xpath("//p[contains(text(),'%s')]/following::p[1]/text()" % u"Условия отпуска из аптек").extract())

            item['drugForm'] = re.sub('[\n\t\r]', '',drugForm.strip())
            item['drugContent'] = re.sub('[\n\t\r]', '',drugContent.strip())
            item['drugProperties'] = re.sub('[\n\t\r]', '',drugProperties.strip())
            item['drugIndication'] = re.sub('[\n\t\r]', '',drugIndication.strip())
            item['drugDosage'] = re.sub('[\n\t\r]', '',drugDosage.strip())
            item['drugSide'] = re.sub('[\n\t\r]', '',drugSide.strip())
            item['drugContrIndication'] = re.sub('[\n\t\r]', '',drugContrIndication.strip())
            item['drugInteractions'] = re.sub('[\n\t\r]', '',drugInteractions.strip())
            item['drugSpecial'] = re.sub('[\n\t\r]', '',drugSpecial.strip())
            item['drugExpiry'] = re.sub('[\n\t\r]', '',drugExpiry.strip())
            item['drugRetailCondition'] = re.sub('[\n\t\r]', '',drugRetailCondition.strip())

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