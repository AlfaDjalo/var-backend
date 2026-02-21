def calculate_greeks(request: GreeksRequest) -> GreeksResponse:
    portfolio = build_portfolio_from_request(request.products)

    engine = GreeksEngine(
        portfolio=portfolio,
        market_data=request.market_data,
        requested_greeks=request.greeks
    )

    result = engine.calculate()

    return GreeksResponse(**result)
