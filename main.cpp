//
// Created by royalconda on 28/05/2024.
//
#include "crow_all.h"
#include "json.hpp"

using json = nlohmann::json;

int main()
{
    crow::SimpleApp app;

    CROW_ROUTE(app, "/add_bet").methods("POST"_method)
            ([](const crow::request& req) {
                auto x = crow::json::load(req.body);
                if (!x)
                {
                    return crow::response(400, "Invalid JSON");
                }



                return crow::response(201, "Bet created successfully");
            });
}