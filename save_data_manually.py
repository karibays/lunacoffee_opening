import pandas as pd
from loguru import logger


class Saver:
    def save_user_data_manually(self, values):
        try:
            df = pd.read_excel('data/reviews.xlsx')
        except:
            logger.error("Failed to read 'reviews' file. Check it out!!!")
            return

        try:
            df.loc[len(df)] = values[0]
            df.to_excel("data/reviews.xlsx", index=False)
            logger.success("Saved user data manually.")
        except:
            logger.error("Failed to save user data manually. Check it out!!!")