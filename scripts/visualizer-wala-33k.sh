python -m grubengeraet.visualizer -p data.json -o "images/topnpie_posts.png" -f top_n_pie
python -m grubengeraet.visualizer -p data.json -o "images/topnpie_words.png" -f top_n_pie -fo "criterion:words"
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_posts.png" -f yearly_top_n_barh_percent -fo "n:8"
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_words.png" -f yearly_top_n_barh_percent -fo "n:8;criterion:words"
python -m grubengeraet.visualizer -p data.json -o "images/posts_per_month.png" -f posts_per_x_bar
python -m grubengeraet.visualizer -p data.json -o "images/posts_per_year.png" -f posts_per_x_bar -fo "x:year"
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_rules.png" -f top_n_bar -fo "criterion:rule_violations"
python -m grubengeraet.visualizer -p data.json -o "images/rv_table.txt" -f rule_violation_bbtable_np
python -m grubengeraet.visualizer -p data.json -o "images/topnpie_emojis.png" -f emojis_pie_top_n
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_emoji_dist.png" -f emoji_distribution_top_n -fo "n_emojis:9"
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_mentioned.png" -f top_n_mentioned_barh
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_mentions.png" -f top_n_mentions_barh
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_quoted.png" -f top_n_quoted_barh
python -m grubengeraet.visualizer -p data.json -o "images/topnbar_quotes.png" -f top_n_quotes_barh
python -m grubengeraet.visualizer -p data.json -o "images/prediction_40k_alltime.png" -f prediction_line -fo "goal:40000;data_period_start:1;data_period_end:32999;data_period_type:post"
python -m grubengeraet.visualizer -p data.json -o "images/prediction_40k_6months.png" -f prediction_line -fo "goal:40000;data_period_start:1778796000;data_period_end:1794776350;data_period_type:timestamp;description:anhand der letzten 6 Monate"
python -m grubengeraet.visualizer -p data.json -o "images/authors_per_year.png" -f authors_per_year_bar
python -m grubengeraet.visualizer -p data.json -o "images/posts_per_author.png" -f posts_per_author_per_year_bar
python -m grubengeraet.visualizer -p data.json -o "images/words_per_post.png" -f top_n_words_per_message_bar
python -m grubengeraet.visualizer -p data.json -o "images/letter_occurrences.png" -f letter_occurrences_bar
