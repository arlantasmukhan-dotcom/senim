# KazTruth benchmark — 79 labeled claims, mode=deep, cascade=on

Weights: default priors (not yet trained) · wall time 623s
SENIM cost: 815 LLM calls (≈10.3 per claim) · $1.572 (≈$0.0199 per claim) · median 32.0s per claim
Settled by sources alone (witness sensors skipped): 14/79

Task: flag FALSE claims (positive class = false claim).

## All claims

| System | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|
| Single LLM (baseline) | 0.45 | 0.486 | 0.468 | 0.481 |
| SENIM alibi only | 0.771 | 0.73 | 0.75 | 0.772 |
| SENIM all sensors | 0.679 | 0.973 | 0.8 | 0.772 |

## Held-out test split (79 claims, never used for tuning)

| System | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|
| Single LLM (baseline) | 0.45 | 0.486 | 0.468 | 0.481 |
| SENIM alibi only | 0.771 | 0.73 | 0.75 | 0.772 |
| SENIM all sensors | 0.679 | 0.973 | 0.8 | 0.772 |

## F1 by popularity

| popularity | n | baseline F1 | SENIM F1 |
|---|---|---|---|
| famous | 21 | 0.609 | 0.947 |
| known | 26 | 0.519 | 0.828 |
| rare | 32 | 0.296 | 0.714 |

## F1 by lang

| lang | n | baseline F1 | SENIM F1 |
|---|---|---|---|
| en | 23 | 0.364 | 0.636 |
| kk | 13 | 0.308 | 0.857 |
| ru | 43 | 0.571 | 0.852 |

## F1 by kind

| kind | n | baseline F1 | SENIM F1 |
|---|---|---|---|
| birth | 25 | 0.417 | 0.929 |
| death | 12 | 0.571 | 0.875 |
| founded | 26 | 0.462 | 0.64 |
| place | 16 | 0.462 | 0.762 |

## Per claim

| id | gold | SENIM | P(wrong) | baseline | calls |
|---|---|---|---|---|---|
| wd002 | true | suspicious | 0.953 | UNSURE | 13 |
| wd004 | true | confirmed | 0.1809 | UNSURE | 12 |
| wd006 | false | contradicted | 0.9884 | FALSE | 12 |
| wd007 | true | unconfirmed | 0.5923 | UNSURE | 12 |
| wd011 | true | contradicted | 0.9777 | FALSE | 12 |
| wd014 | false | contradicted | 0.9895 | FALSE | 2 |
| wd017 | true | unconfirmed | 0.8891 | UNSURE | 13 |
| wd018 | false | suspicious | 0.9038 | UNSURE | 12 |
| wd022 | true | contradicted | 0.9891 | UNSURE | 13 |
| wd023 | true | unconfirmed | 0.4436 | FALSE | 12 |
| wd024 | true | suspicious | 0.9337 | FALSE | 12 |
| wd025 | true | confirmed | 0.251 | UNSURE | 12 |
| wd026 | true | confirmed | 0.2366 | FALSE | 12 |
| wd027 | false | contradicted | 0.9791 | FALSE | 12 |
| wd029 | true | confirmed | 0.1204 | FALSE | 12 |
| wd031 | false | contradicted | 0.9992 | FALSE | 12 |
| wd041 | true | confirmed | 0.1295 | FALSE | 2 |
| wd047 | true | unconfirmed | 0.9713 | TRUE | 12 |
| wd048 | true | confirmed | 0.2387 | FALSE | 12 |
| wd049 | false | contradicted | 0.9791 | FALSE | 12 |
| wd052 | false | suspicious | 0.8818 | UNSURE | 13 |
| wd054 | true | unconfirmed | 0.624 | FALSE | 12 |
| wd055 | false | suspicious | 0.8971 | FALSE | 13 |
| wd056 | false | contradicted | 0.9991 | UNSURE | 13 |
| wd060 | false | contradicted | 0.9569 | UNSURE | 12 |
| wd061 | true | confirmed | 0.1792 | UNSURE | 12 |
| wd066 | false | contradicted | 0.9891 | UNSURE | 12 |
| wd068 | false | contradicted | 0.9984 | UNSURE | 12 |
| wd073 | false | contradicted | 0.9674 | UNSURE | 12 |
| wd074 | true | suspicious | 0.8313 | FALSE | 12 |
| wd079 | false | suspicious | 0.8688 | FALSE | 12 |
| wd080 | false | contradicted | 0.9918 | UNSURE | 2 |
| wd082 | false | contradicted | 0.9844 | FALSE | 12 |
| wd083 | false | contradicted | 0.9895 | FALSE | 2 |
| wd084 | false | contradicted | 0.997 | UNSURE | 11 |
| wd090 | true | suspicious | 0.7191 | FALSE | 12 |
| wd094 | true | confirmed | 0.1039 | UNSURE | 12 |
| wd096 | false | contradicted | 0.975 | FALSE | 13 |
| wd100 | true | unconfirmed | 0.3597 | FALSE | 13 |
| wd101 | true | suspicious | 0.953 | UNSURE | 13 |
| wd107 | false | contradicted | 0.9992 | FALSE | 12 |
| wd108 | false | contradicted | 0.9926 | FALSE | 12 |
| wd109 | true | suspicious | 0.702 | UNSURE | 12 |
| wd110 | false | contradicted | 0.9895 | UNSURE | 2 |
| wd113 | false | contradicted | 0.9895 | FALSE | 2 |
| wd117 | false | contradicted | 0.9884 | UNSURE | 11 |
| wd118 | true | unconfirmed | 0.7878 | TRUE | 12 |
| wd120 | false | suspicious | 0.9276 | FALSE | 12 |
| wd121 | false | contradicted | 0.9895 | FALSE | 2 |
| wd122 | false | suspicious | 0.908 | UNSURE | 12 |
| wd123 | false | contradicted | 0.9933 | TRUE | 2 |
| wd124 | true | suspicious | 0.9226 | FALSE | 11 |
| wd127 | true | suspicious | 0.7225 | UNSURE | 11 |
| wd128 | true | suspicious | 0.9605 | FALSE | 12 |
| wd129 | false | contradicted | 0.9878 | FALSE | 8 |
| wd130 | false | contradicted | 0.9955 | UNSURE | 12 |
| wd138 | true | confirmed | 0.3494 | FALSE | 12 |
| wd141 | true | suspicious | 0.7376 | FALSE | 12 |
| wd143 | false | unconfirmed | 0.6704 | UNSURE | 13 |
| wd144 | true | confirmed | 0.1295 | FALSE | 2 |
| wd148 | true | confirmed | 0.1295 | FALSE | 2 |
| wd152 | true | suspicious | 0.7726 | UNSURE | 12 |
| wd159 | true | suspicious | 0.887 | UNSURE | 13 |
| wd160 | false | suspicious | 0.9198 | UNSURE | 12 |
| wd162 | false | contradicted | 0.9895 | FALSE | 2 |
| wd163 | true | unconfirmed | 0.4093 | TRUE | 12 |
| wd164 | true | contradicted | 0.9918 | UNSURE | 2 |
| wd167 | false | contradicted | 0.9963 | UNSURE | 12 |
| wd168 | true | unconfirmed | 0.9005 | UNSURE | 13 |
| wd171 | true | confirmed | 0.0949 | FALSE | 2 |
| wd172 | true | suspicious | 0.9498 | FALSE | 12 |
| wd173 | false | contradicted | 0.9973 | UNSURE | 13 |
| wd176 | true | contradicted | 0.9852 | FALSE | 12 |
| wd187 | true | confirmed | 0.2812 | FALSE | 12 |
| wd191 | true | confirmed | 0.156 | TRUE | 12 |
| wd193 | true | confirmed | 0.1182 | UNSURE | 2 |
| wd194 | false | suspicious | 0.9248 | UNSURE | 13 |
| wd195 | false | suspicious | 0.9408 | FALSE | 13 |
| wd196 | true | unconfirmed | 0.6799 | FALSE | 12 |

⚠️ Only 79 claims: numbers are indicative, not statistically solid. Aim for 200.
