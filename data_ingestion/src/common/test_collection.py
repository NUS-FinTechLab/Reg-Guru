from common.embedding_helper import query_texts
if __name__ == "__main__":
    """32021R1230"""
    # questions = [
    #     "A payment institution operating in the euro area wants to provide transparency on charges for cross-border payments denominated in euro to its retail clients. What specific information must be disclosed before the payment transaction is executed, and under which circumstances must this information be updated?",
    #     "A financial compliance officer discovers that a domestic euro payment is being charged differently than an equivalent cross-border euro payment to another Member State. Under EU rules, can this practice be justified?",
    #     "A corporate treasury department frequently makes transfers from accounts in non-euro EU Member States. How should it ensure compliance with disclosure obligations when currency conversion is involved?"
    # ]
    # answer_gpt = [
    #     "Before executing a payment transaction, the payment service provider must inform the payer of the charges applicable and, if applicable, the exchange rate used for converting the payment into another currency. This information must be provided in a clear and comprehensible form, and any changes to charges or exchange rates must be communicated in advance. Updates are required whenever such costs or rates change. (Source: Article 3(1)–(2) of Regulation (EU) 2021/1230)",
    #     "No. Under EU law, charges for cross-border payments in euro must be the same as those applied to corresponding national payments of the same value and type within the Member State. Differentiating between domestic and cross-border euro transactions violates the principle of charge equivalence. (Source: Article 3(1) — Principle of equality of charges)",
    #     "When payments involve currency conversion, the service provider must disclose the total currency conversion charges, including the mark-up over the latest available European Central Bank reference rate. These details must be presented as a percentage difference and communicated before the transaction is authorized to ensure transparency and allow informed decision-making. (Source: Article 5(4)–(5) — Transparency on currency conversion charges)"
    # ]
    # results = query_texts(questions, collection_name='eurlex_test', n_results=3)
    

    # """_Act_AA2004"""
    # questions = ["What is voting share of an enterprise?"]
    # results = query_texts(questions, collection_name="test", n_results=3)

    """resources_advisories_fincen_advisory_fin_2025_a003_fincen_advisory_cmln_508"""
    questions = ["List recommended methods to alert activities that is tied to Chinese Money Laundering Network."]
    results = query_texts(questions, collection_name="test", n_results=3)
    
    print(results)