```yaml
jobs:
  tag-alert:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0

      - name: Publish Tag Notification
        uses: inmar/actions-sns-tag-alert@master
        with:
          aws_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws_secret_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          topic_arn: "arn:aws:sns:us-east-1:0123456789012:event_topic"
          tag_pattern: '^v?\d+\.\d+\.\d+$'
```

Note that it is important to use single quotes on the tag_pattern field. The YAML parser will get angry, otherwise.
