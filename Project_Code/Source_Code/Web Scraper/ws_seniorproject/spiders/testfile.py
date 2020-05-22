import scrapy, re
from scrapy.crawler import CrawlerProcess
from ws_seniorproject.items import WsSeniorprojectItem

class TestfileSpider(scrapy.Spider):
    
    # start section 1:
    # user search input
    # this allows users to input the items they would like to search for (i.e shoes, pants, tv's).
    # Amazon's url for a search looks like this: https://www.amazon.com/s?k= 
    # if we want to search for shoes, we add 'shoes' at the end of this usrl (https://www.amazon.com/s?k=shoes)
    # if the search is more than one word (i.e 'nike shoes', 'khaki pants'), the url requires a '+' between words
    # example: user input = nike shoes 
    # url = https://www.amazon.com/s?k=nike+shoes
    # the following code will generate such url and input it into 'start_urls'

    name = 'testfile'
    allowed_domains = ['amazon.com']
    search_terms = input("Enter search term: ")
    print("Search term: " + search_terms)
    
    search_terms_list = search_terms.split()
    
    if len(search_terms_list) == 1:
        url_to_crawl = 'https://www.amazon.com/s?k=' + search_terms
    else:
        url_to_crawl = 'https://www.amazon.com/s?k=' + search_terms_list[0]
        for terms in search_terms_list[1:]:
            url_to_crawl = url_to_crawl + "+" + terms

    # start_urls is the list of urls scrapy automatically looks for to crawl when the program is run. We are only
    # feeding it one url: the one generated by our code above. 

    start_urls = [url_to_crawl]

    # end section 1

    # start section 2
    # the follwowing function is the default parsing function called by scrapy to crawl the urls in 'start_urls'
    # the function tells scrapy what to scrape from the url. For this project, multiple urls have to be crawled:

    def parse(self, response):
        
        # the follwing line of code will look for all product urls after we search for a product. Amazon lists about 50-60
        # products for every search. However, as of now we are asking scrapy to extract the first 9 product urls [0:9]
        # and store them in a list named 'urls'

        # bug that was fixed: the code generated a url and an unwanted duplicate of the url. This was fixed by combining
        # css and xpath selectors to look for an h2 tag with the classes a-size-mini, a-spacing-none, and s-line-clamp-2
        # the xpath selector would then look for the href value and return the url. The duplicate urls came from not including
        # the classes in the h2 tag above the href value.

        urls = response.css('h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2 a').xpath('@href')[0:9].extract()
        
        # each url from the list 'urls' must individually be crawled. To allow for this, we run a for-loop that will
        # send a request to crawl a new url. For each url crawl request, we call the function 'parse_link'. 
        # parse_link will tell scrapy what we want to scrape from each url containing our individual products.  
        
        for product in urls:
            product_url = "https://www.amazon.com" + product
            request = scrapy.Request(product_url, callback=self.parse_link)
            yield request    

    # end section 2

    # start section 3
    # the following function 'parse_link' is called for every product. It currently scrapes the following fields:
    # 
    # product name
    # product price
    # product rating (out of 5 stars)
    # number of ratings
    # percent of ratings that are 5 stars
    # percent of ratings that are 4 stars
    # percent of ratings that are 3 stars
    # percent of ratings that are 2 stars
    # percent of ratings that are 1 stars

    # bugs that were fixed:
    # product name returned multiple spaces and '\n' fields along with the text for the product name. This was fixed by
    # simply calling the .strip() function on the extracted result. To allow the .strip() function to be added, 'title'
    # had to return a string instead of a list, which was made possible by adding '[0]' to the code, returning the first
    # value in the list as a string. This was convenient as all the other values following product name 
    # also returned strings.

    # percents of 1 - 5 stars was not returning the right values. This was fixed by combining css and xpath selectors
    # to allow the 'aria-label' to be selected. Additionally, the 6th - 10th values in the list returned the values we 
    # needed, which is why these are called in order: 5, 6, 7, 8, and 9.

    def parse_link(self, response):
        items = WsSeniorprojectItem()

        test = response.css('ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none li span.a-list-item span::text').extract()

        order = 0
        found_dimension = False
        found_first_listed = False
        for elements in test:
            if elements == "Product Dimensions:\n                    ": 
                product_dimensions = test[order + 1] 
                found_dimension = True                
            elif elements == "ASIN:\n                    ":
                asin_number = test[order + 1]
            elif elements == "Date first listed on Amazon:\n                    ":
                first_listed =test[order + 1]
                found_first_listed = True
            order = order + 1

        ## days since first listed
        if found_first_listed:
            import datetime

            fl = first_listed.replace(',','')
            fl = fl.split()
            month = fl[0]
            listed_day = int(fl[1])
            listed_year = int(fl[2])
            if month == 'January':
                listed_month = int(1)
            elif month == 'February':
                listed_month = int(2)
            elif month == 'March':
                listed_month = int(3)
            elif month == 'April':
                listed_month = int(4)
            elif month == 'May':
                listed_month = int(5)
            elif month == 'June':
                listed_month = int(6)
            elif month == 'July':
                listed_month = int(7)
            elif month == 'August':
                listed_month = int(8)
            elif month == 'September':
                listed_month = int(9)
            elif month == 'October':
                listed_month = int(10)
            elif month == 'November':
                listed_month = int(11)
            else:
                listed_month = int(12)
            
            current_time = datetime.datetime.now()
            current_day = int(current_time.strftime('%d'))
            current_month = int(current_time.strftime('%m'))
            current_year = int(current_time.strftime('%Y'))

            days = (current_year - listed_year) * 365
            days = days + ((current_month - listed_month) * 30)
            days = days + (current_day - listed_day)
            items['Days_Since_First_Listed'] = days
            
            listed_format = str(listed_month) + "/" + str(listed_day) + "/" + str(listed_year)
            items['First_Listed_Formatted'] = listed_format

        try:
            title = response.css('span.a-size-large#productTitle::text')[0].extract().strip(' \n')
        except IndexError:
            title = ''

        try:
            price = response.css('span.a-size-medium.a-color-price.priceBlockBuyingPriceString#priceblock_ourprice::text')[0].extract()
        except IndexError:
            price = ''

        try:
            low_price_pre1 = response.css('span.a-size-medium.a-color-price.priceBlockBuyingPriceString#priceblock_ourprice::text')[0].extract()
            low_price_pre2 = low_price_pre1.split()
            low_price = low_price_pre2[0].strip('$')
            low_price = float(low_price)
        except IndexError:
            low_price = ''

        try:
            high_price_pre1 = response.css('span.a-size-medium.a-color-price.priceBlockBuyingPriceString#priceblock_ourprice::text')[0].extract()
            high_price_pre2 = high_price_pre1.split()
            high_price = high_price_pre2[2].strip('$')
            high_price = float(high_price)
        except IndexError:
            high_price = ''

        try:
            rating_pre1 = response.css('span.a-icon-alt::text')[0].extract()
            rating_pre2 = rating_pre1.split()
            rating = rating_pre2[0]
            rating = float(rating)
        except IndexError:
            rating = ''

        try:
            rating_count_pre1 = response.css('span.a-size-base#acrCustomerReviewText::text')[0].extract()
            rating_count_pre2 = rating_count_pre1.split()[0]
            rating_count_pre3 = rating_count_pre2.replace(',', '')
            rating_count = int(rating_count_pre3)
        except IndexError:
            rating_count = ''

        #percent_5_star = response.css('div.a-meter').xpath('@aria-label')[5].extract()
        try:
            percent_5_star_pre = response.css('td.a-text-right span.a-size-base a.a-link-normal::text')[0].extract().strip(' \n')
            percent_5_star = percent_5_star_pre.strip('%')
            percent_5_star = int(percent_5_star)
        except IndexError:
            percent_5_star = ''

        #percent_4_star = response.css('div.a-meter').xpath('@aria-label')[6].extract()
        try: 
            percent_4_star_pre = response.css('td.a-text-right span.a-size-base a.a-link-normal::text')[1].extract().strip(' \n')
            percent_4_star = percent_4_star_pre.strip('%')
            percent_4_star = int(percent_4_star)
        except IndexError:
            percent_4_star = ''

        #percent_3_star = response.css('div.a-meter').xpath('@aria-label')[7].extract()
        try: 
            percent_3_star_pre = response.css('td.a-text-right span.a-size-base a.a-link-normal::text')[2].extract().strip(' \n')
            percent_3_star = percent_3_star_pre.strip('%')
            percent_3_star = int(percent_3_star)
        except IndexError:
            percent_3_star = ''

        #percent_2_star = response.css('div.a-meter').xpath('@aria-label')[8].extract()
        try: 
            percent_2_star_pre = response.css('td.a-text-right span.a-size-base a.a-link-normal::text')[3].extract().strip(' \n')
            percent_2_star = percent_2_star_pre.strip('%')
            percent_2_star = int(percent_2_star)
        except IndexError:
            percent_2_star = ''

        #percent_1_star = response.css('div.a-meter').xpath('@aria-label')[9].extract()
        try:
            percent_1_star_pre = response.css('td.a-text-right span.a-size-base a.a-link-normal::text')[4].extract().strip(' \n')
            percent_1_star = percent_1_star_pre.strip('%')
            percent_1_star = int(percent_1_star)
        except IndexError:
            percent_1_star = ''
        
        try:
            category = response.css('span.zg_hrsr_ladder a::text').extract()
        except IndexError:
            category = ''

        try:
            rank_pre = response.css('#SalesRank::text')[1].extract().strip(' \n (')
            rank_comma = rank_pre.strip('#').split()[0]
            rank = rank_comma.replace(',','')
            rank = int(rank)

            rank_category = response.css('#SalesRank::text')[1].extract().strip(' \n (')
            rank_category = rank_category.strip('#')
            rank_category = rank_category.replace(rank_comma,'')
            rank_category = rank_category.strip('in ')

        except IndexError:
            rank = ''

        try:
            answered_pre = response.css('a#askATFLink span.a-size-base::text')[0].extract().strip(' \n')
            answered = answered_pre.split()[0]
            answered = int(answered)
        except IndexError:
            answered = ''
        except ValueError:
            answered = 1000

        try:
            prod_desc = response.css('div#productDescription p::text')[0].extract().strip(' \n')
        except IndexError:
            prod_desc = ''

        try:
            descriptMain1 = response.css("ul.a-unordered-list.a-vertical.a-spacing-none span.a-list-item::text").extract()
        except IndexError:
            descriptMain1 = ''

        try:
            descriptMain = descriptMain1[0].strip(' \n\t')
        except IndexError:
            descriptMain = ''

        if len(descriptMain1) > 1:
            for item in descriptMain1[1:]:
                if item != None:
                    descriptMain = descriptMain + ", " + item.strip(' \n\t')

        try:
            if category != None:
                if len(category) == 1:
                    category_final = category
                else:
                    category_final = category[0]
                    for categories in category[1:]:
                        category_final = category_final + ", " + categories
            else:
                category_final = ''
        except IndexError:
            category_final = ''

        if found_dimension == True:
            try:
                dim_len_pre = product_dimensions
                dim_len = dim_len_pre.split()[0]
                dim_len = float(dim_len)
            except IndexError:
                dim_len = ''
        if found_dimension == True:
            try:
                dim_width_pre = product_dimensions
                dim_width = dim_width_pre.split()[2]
                dim_width = float(dim_width)
            except IndexError:
                dim_width = ''
        if found_dimension == True:
            try:
                dim_height_pre = product_dimensions
                dim_height = dim_height_pre.split()[4]
                dim_height = float(dim_height)
            except IndexError:
                dim_height = ''

        try: 
            asin = response.css('ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none li span.a-list-item span::text')[6].extract()
        except IndexError:
            asin = ''

        try:
            fit = response.css('div.a-section a#HIF_link::text')[0].extract().strip('FitsAasexpected %()')
            if fit == '\n':
                fit2 = response.css('div.a-section a#HIF_link span.a-size-base::text')[0].extract().strip('Fits as expected %()')
                fit2 = int(fit2)
                items['Fit_As_Expected'] = fit2
            else:
                fit = int(fit)
                items['Fit_As_Expected'] = fit
        except IndexError:
            fit = 'Fit not available'
            items['Fit_As_Expected'] = fit

        if title != None:
            items['Product'] = title
        else:
            items['Product'] = ''
        
        if price != None:
            items['Price'] = price
        else:
            items['Price'] = ''

        items['Low_Price'] = low_price
        items['High_Price'] = high_price
        
        if rating != None:
            items['Rating'] = rating
        else:
            items['Rating'] = ''
        
        if rating_count != None:
            items['Rating_Count'] = rating_count
        else:
            items['Rating_Count'] = ''
        
        if percent_5_star != None:
            items['Five_Stars'] = percent_5_star
        else:
            items['Five_Stars'] = ''        
        if percent_4_star != None:
            items['Four_Stars'] = percent_4_star
        else: 
            items['Four_Stars'] = ''
        
        if percent_3_star != None:
            items['Three_Stars'] = percent_3_star
        else: 
            items['Three_Stars'] = ''
        
        if percent_2_star != None:
            items['Two_Stars'] = percent_2_star
        else:
            items['Two_Stars'] = ''

        if percent_1_star != None:
            items['One_Star'] = percent_1_star
        else:
            items['One_Star'] = ''

        items['Category'] = category_final
        
        if rank != None:
            items['Sales_Rank'] = rank
        else: 
            items['Sales_Rank'] = ''

        try:
            items['Rank_Category'] = rank_category
        except UnboundLocalError:
            items['Rank_Category'] = ''

        try:
            items['Answered_Questions'] = answered
        except UnboundLocalError:
            items['Answered_Questions'] = ''
            
        items['Description_Main'] = descriptMain.strip(' ,')
        items['Description_Product'] = prod_desc
        
        try:
            items['Dimensions'] = product_dimensions
        except UnboundLocalError:
            items['Dimensions'] = ''

        try:
            items['Dimensions_Length'] = dim_len
        except UnboundLocalError:
            items['Dimensions_Length'] = ''

        try:
            items['Dimensions_Width'] = dim_width
        except UnboundLocalError:
            items['Dimensions_Width'] = ''

        try:
            items['Dimensions_Height'] = dim_height
        except UnboundLocalError:
            items['Dimensions_Height'] = ''

        try: 
            items['ASIN_Number'] = asin_number
        except UnboundLocalError:
            items['ASIN_Number'] = ''

        try:
            items['First_Listed'] = first_listed
        except UnboundLocalError:
            items['First_Listed'] = ''

        #items['Prime'] = product_dimensions

        yield items

    # end section 3

#process = CrawlerProcess({'USER_AGENT': 'Mozilla/5.0', 'FEED_FORMAT': 'json', 'FEED_URI': 'data.json'})
#process.crawl(TestfileSpider)
#process.start()
