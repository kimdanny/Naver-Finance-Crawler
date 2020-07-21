from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import os


# TODO: crawl by dates range ex) crawl news from when to when
# TODO: Use multiprocessing to speed up crawler

class Naver_Crawler:

    def __init__(self, company_code):
        self.company_code = company_code
        assert type(self.company_code) == str

        # TODO: Directory and files auto-generation, auto-deletion
        # dirname = os.path.dirname(__file__)
        # target_dir = os.path.join(dirname, self.company_code)
        # self.filename = os.path.join(dirname, self.company_code+".csv")

    def crawl_news(self, maxpage, page_to_csv=True, full_pages_to_csv=True):
        page = 1
        assert type(maxpage) == int

        result_df = None

        while page <= maxpage:

            # https://finance.naver.com/item/news.nhn?code=095570&page=2&sm=entity_id.basic  ==> 095570 종목 2페이지 기사 sample url
            url = 'https://finance.naver.com/item/news_news.nhn?code=' + self.company_code + '&page=' + str(
                page) + '&sm=entity_id.basic'

            html_text = requests.get(url).text
            html = BeautifulSoup(html_text, "html.parser")

            # Possible future Error Handling: maxpage Error -> Currently handled by Naver themself
            # 실제 웹에는 5페이지까지 밖에 없는데 maxpage를 10으로 설정한 경우 5페이지에서 loop break 시킴
            try:
                print(f'Current page: {page}')
                current_page_on_html = html.select('.on')[1].text.replace("\n", "").replace("\t", "")
            except IndexError:
                current_page_on_html = page
            if current_page_on_html != str(page):
                break

            # 1. ==Date==
            dates = html.select('.date')
            date_result = [date.get_text() for date in dates]

            # 2. ==Source==
            sources = html.select('.info')
            source_result = [source.get_text() for source in sources]

            # 3. ==Title==
            titles = html.select('.title')
            title_result = []
            for title in titles:
                title = title.get_text()
                title = re.sub('\n', '', title)
                title_result.append(title)

            # 4. ==Link==
            links = html.select('.title')

            link_result = []
            article_body_result = []
            for link in links:
                article_url = 'https://finance.naver.com' + link.find('a')['href']
                link_result.append(article_url)

                # 5. ==Body==
                article_html_text = requests.get(article_url).text
                article_html = BeautifulSoup(article_html_text, "html.parser")

                body = article_html.find('div', id='news_read')
                body = body.text  # type --> sting
                body = body.replace("\n", "").replace("\t", "")
                # print(body)
                # TODO: body내 특수문자 다 없애기
                article_body_result.append(body)

                # 6. ==Reaction==
                reaction_space = article_html.find('ul', class_='u_likeit_layer _faceLayer')
                # print(reaction_space)
                good_reaction_count = int(reaction_space.find('li', class_='u_likeit_list good') \
                                          .find('span', class_='u_likeit_list_count _count').text)


                warm_reaction_count = int(reaction_space.find('li', class_='u_likeit_list warm') \
                                          .find('span', class_='u_likeit_list_count _count').text)

                sad_reaction_count = int(reaction_space.find('li', class_='u_likeit_list sad') \
                                         .find('span', class_='u_likeit_list_count _count').text)

                angry_reaction_count = int(reaction_space.find('li', class_='u_likeit_list angry') \
                                           .find('span', class_='u_likeit_list_count _count').text)

                want_reaction_count = int(reaction_space.find('li', class_='u_likeit_list want') \
                                          .find('span', class_='u_likeit_list_count _count').text)


                print(reaction_space)
                print("="*20)

                # 7. ==Commentary==
                comments = article_html.find_all(lambda tag: tag.name == 'span' and tag.get('class') == 'u_cbox_contents')
                #print(comments)

            # To Dataframe and To CSV (optional)
            page_result = {
                "Date": date_result, "Source": source_result, "Title": title_result,
                "Link": link_result, "Body": article_body_result,
                "good_count": good_reaction_count,
                "warm_count": warm_reaction_count,
                "sad_count": sad_reaction_count,
                "angry_count": angry_reaction_count,
                "want_count": want_reaction_count
            }

            page_df = pd.DataFrame(page_result)

            if result_df is None:
                result_df = page_df
            else:
                # bind page_df at the bottom of the result_df
                result_df = result_df.append(page_df, ignore_index=True)

            if page_to_csv:
                page_df.to_csv(self.company_code + 'page' + str(page) + '.csv', mode='w',
                               encoding='utf-8-sig')  # 한글 깨짐 방지 인코딩

            page += 1

        if full_pages_to_csv:
            result_df.to_csv(self.company_code + '.csv', mode='w', encoding='utf-8-sig')  # 한글 깨짐 방지 인코딩

        return result_df

    # TODO: Research 크롤링.
    def crawl_research(self, maxpage, page_to_csv=True, full_pages_to_csv=True):
        # TODO: 아래는 종목별 리서치 parameterised url
        # https://finance.naver.com/research/company_list.nhn?keyword=&searchType=itemCode&itemCode=105560
        page = 1
        assert type(maxpage) == int

        result_df = None

        while page <= maxpage:
            url = 'https://finance.naver.com/research/company_list.nhn?keyword=&searchType=itemCode&itemCode=' \
                            + self.company_code + '&page=' + str(page)


if __name__ == '__main__':
    # 종목 코드로 기사 크롤링 --> 종목코드는 FinancialDataReader에서 받아온다.
    # sample code --> {'005930': '삼성전자',
                    #  '005380': '현대차',
                    #  '015760': '한국전력',
                    #  '005490': 'POSCO',
                    #  '105560': 'KB금융'
                    #  '95570' : 'AJ네트웍스'}

    naver_crawler = Naver_Crawler('005930')
    sample_df = naver_crawler.crawl_news(maxpage=13)
    # print(sample_df)
