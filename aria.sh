export MAX_DOWNLOAD_SPEED=0
export MAX_CONCURRENT_DOWNLOADS=7

aria2c --enable-rpc --rpc-listen-all=false --check-certificate=false \
   --max-connection-per-server=10 --rpc-max-request-size=1024M \
   --follow-torrent=mem --split=10 \
   --daemon=true --allow-overwrite=true --max-overall-download-limit=$MAX_DOWNLOAD_SPEED \
   --max-overall-upload-limit=1K --max-concurrent-downloads=$MAX_CONCURRENT_DOWNLOADS \
   --max-file-not-found=0 --max-tries=20 --auto-file-renaming=true \
   --seed-time=0.01 --seed-ratio=1.0 \
   --content-disposition-default-utf8=true --http-accept-gzip=true --reuse-uri=true --netrc-path=/usr/src/app/.netrc
