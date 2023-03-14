import time
import re
import numpy as np
import pandas as pd
import traceback
import streamlit as st
from langdetect import detect
import plotly.express as px
import plotly.graph_objects as go
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')


from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

st.set_page_config(layout='wide')
col1,col2,col3 = st.columns([2,2,2])

#
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    return scores
#

with col1:
    st.header("Amazon 3 Star Reviews - Sentiment Analysis")
    st.markdown("<p style='text-align: justify;'>This app takes a product given by the user as input. It retrieves the first result on Amazon and collects all the 3-star reviews. Language detection is then performed, and text analysis is carried out only on the reviews written in English using VADER. The app determines whether the 3-star reviews are closer to positive or negative ones. It also fetches the bar chart found on Amazon and presents an explanatory polar graph.<p>", unsafe_allow_html=True)

    search_text = st.text_area("",placeholder='Enter product')

    if st.button("Search"):
        try:
            driver.quit()
        except:
            print('\n Driver already Closed \n ')

        #driver = webdriver.Chrome()
        driver = webdriver.Safari(executable_path='/usr/bin/safaridriver')
        driver.implicitly_wait(3)
        driver.maximize_window()


        driver.get('https://www.amazon.com')
        time.sleep(1.5)

        search_bar = driver.find_element(By.XPATH, '//*[@id="twotabsearchtextbox"]')

        search_bar.send_keys(search_text)

        search_btn = driver.find_element(By.XPATH, '//*[@id="nav-search-submit-button"]')
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(1.5)

        try:
            title = driver.find_elements(By.CSS_SELECTOR,'.a-size-medium.a-color-base.a-text-normal')[0]
            time.sleep(1.5)
            rev_num = driver.find_elements(By.CSS_SELECTOR,'.a-size-base.s-underline-text')[0].get_attribute('innerText').replace(',','').replace('(','').replace(')','')
            with col2:
                st.markdown(title.get_attribute('innerText')+' |  Total reviews: '+rev_num,unsafe_allow_html=True)
            driver.execute_script("arguments[0].click();", title)
            time.sleep(1.5)

            rev_url = driver.current_url+'/#customer-reviews_feature_div'
            driver.get(rev_url)
            time.sleep(1.5)


            # amazon refuses the connection for this:
            # iframe_height = 500
            # iframe_width = 700
            # st.markdown(f"<iframe src='{rev_url}' frameborder='1'></iframe>",unsafe_allow_html=True)


            # rev_bars = driver.find_element(By.CSS_SELECTOR, '.a-fixed-left-grid.a-spacing-none').get_attribute('outerHTML')
            rev_bars = driver.find_element(By.CSS_SELECTOR, '.a-fixed-left-grid.a-spacing-none').get_attribute('innerText')
            lines = rev_bars.split('\n')
            lst = [[lines[i].replace('\t', ''), lines[i+1]] for i in range(0, len(lines)-1, 2)]
            arr_clean = np.array([[s.replace('%', '') for s in sub_arr] for sub_arr in lst])

            ht=[i + '%' for i in list(reversed(list(arr_clean[:, 1])))]
            fig = go.Figure(go.Bar(
                x=list(reversed(list(arr_clean[:,1]))),
                y=list(reversed(['5 Stars','4 Stars','3 Stars','2 Stars','1 Star'])),
                orientation='h')
            )
            fig.update_xaxes(title_text='Percentage')
            fig.update_traces(hovertext=ht,hovertemplate='')





            star3_but = driver.find_element(By.XPATH, "//*[contains(@title, '3 stars')]")
            driver.execute_script("arguments[0].click();", star3_but)
            time.sleep(1.5)

            rev_all=[]
            while True:
                try:
                    rev_text_node = driver.find_elements(By.CSS_SELECTOR, ".a-size-base.review-text.review-text-content")
                    rev_text=[t.get_attribute('innerText') for t in rev_text_node]
                    rev_all=rev_all+rev_text
                    next_but = driver.find_element(By.XPATH, "//*[@id='cm_cr-pagination_bar']/ul/li[2]/a")
                    driver.execute_script("arguments[0].click();", next_but)
                    time.sleep(1.5)
                except:
                    print('Gathered')
                    break

            if rev_all==[]:
                with col2:
                    st.write('No 3 star reviews found')
            else:
                rev_all_clean = [x for x in rev_all if x != '']
                rev_all_english=[x for i,x in enumerate(rev_all_clean) if detect(rev_all_clean[i])=='en']


                scores_arr =np.array([analyze_sentiment(x)['compound'] for x in rev_all_english ])
                mean_score = np.round(np.mean(scores_arr), 4)
                scores = list(scores_arr)
                # scores.sort(reverse=True)

                with col2:
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


                with col3:
                    st.write('Mean score from 3 star reviews: ' + str(mean_score))
                    if mean_score>0 and mean_score<0.5: comment='(Slightly positive)'
                    if mean_score>0.5: comment='(Positive)'
                    if mean_score<0 and mean_score>-0.5: comment='(Slightly negative)'
                    if mean_score<-0.5: comment='(Negative)'
                    st.write(comment)

                    fig=px.line_polar(r=scores,theta=range(0,360,int(360/len(scores))),range_theta=[0,360],range_r=[-1,1],line_close=True)
                    fig.update_traces(
                            mode="lines+markers",
                            fill='toself',
                            fillcolor='rgba(0, 0, 255, 0.2)',
                            line_color='rgba(0, 0, 255, 0.2)',
                            showlegend=True,
                            name="Individual Scores")


                    tickvals = [-1, 0, 1]
                    ticktext = ['(-1) Negative', '(0) Neutral', '(+1)Positive']
                    fig.update_layout( polar=dict(angularaxis=dict(tickvals=[],showticklabels=False)))
                    fig.update_layout(polar=dict(radialaxis=dict(tickvals=tickvals,ticktext=ticktext)))

                    # plot score mean circle
                    fig.add_trace(
                        go.Scatterpolar(
                            r=[mean_score]*361,
                            theta=list(range(0,361)),
                            fill='toself',
                            fillcolor='rgba(205, 92, 92, 0.05)', # Choose your own fill color and opacity
                            showlegend=True,
                            name="Mean score",
                            mode="lines",
                            line_color='indianred'
                        )
                    )



                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        except Exception:
            with col3:
               st.write('Error occurred')



# fig.show(renderer="browser")








