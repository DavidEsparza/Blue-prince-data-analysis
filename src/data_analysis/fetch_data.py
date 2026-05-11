from data_pipeline.db_manager import query_db
import pandas as pd


def get_player_runs_data(player_id):
    query = """SELECT 
                    days.day as Day, 
                    days.steps_taken as Steps, 
                    days.items as Items, 
                    days.new_rooms as NewRooms,
                    days.rank_reached as Rank,
                    OuterRoom.title as OuterRoom,
                    COUNT(rooms.number) as RoomsInMansion,
                    GROUP_CONCAT(
                        rooms.number || ',' || rooms.title || ',' || mansions.position_x || ',' || mansions.position_y,
                        ';'
                    ) AS Mansion
               FROM players
               LEFT JOIN days ON days.player = players.id
               LEFT JOIN rooms as OuterRoom ON days.outer_room = OuterRoom.number
               INNER JOIN rooms on mansions.room = rooms.number
               INNER JOIN mansions ON days.id = mansions.day
               WHERE players.id = ?
               GROUP BY days.day"""
    results = query_db(query, (player_id,))
    return results


def get_all_rooms_data():
    query = """SELECT number, title, gem_cost, rarity, shape, GROUP_CONCAT(types.name) as types
               FROM rooms
               LEFT JOIN room_types ON rooms.number = room_types.room
               LEFT JOIN types ON room_types.type = types.id
               GROUP BY number
               """
    results = query_db(query)
    return results
