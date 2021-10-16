#!/bin/bash

file_name="/var/db/backup/$(date +%F)_stock.db.7z"

7z a $file_name /var/db/wide_stock.db /var/db/cifra_stock.db /var/db/bus.db

