pushgateway-prune
----
为什么会有这个仓库，原生的prometheus 的pushgateway并没有支持ttl也就是过期的job删除的功能，但是pushgateway提供删除job的接口所以基于这个接口我们可以做到定时获取pushgateway的过期job将其进行删除以保证grafana的上面的图是正常的

那么不删除过期job会有什么影响，当pushgateway中的job没有最新的数据时prometheus依旧会从pushgateway中拿数据并且作为当前时间的数据，可能这个时候某个主机已经处于down状态但是因为该问题我们会从grafana上面还会看到该主机处于up状态并且告警也会判断错误

----


使用方式：
----

默认环境变量:

|环境变量|默认值|说明|
|---|---|---|
|TTL| 10 | 每10秒拿一次pushgateway的最新数据并且判断所有的job最后更新时间与当前时间比是否大于10s|
|PUSHGATEWAY_URL| | pushgateway 的地址|
|PUSH_WEBHOOK_URL| | webhook 的地址，可以提供mattermost的webhook来将处理的过程发送至频道中|


打包镜像：
```shell script
docker build -t pushgateway-prune .
```

部署pushgateway以及添加sidecar:

```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  annotations:
    image/from: hub.docker.com
    image/name: prom-pushgateway
    image/version: 1.1.0
  labels:
    app: prom-pushgateway
  namespace: ops
  name: prom-pushgateway
spec:
  replicas: 1
  selector:
    matchLabels:
      image/from: hub.docker.com
      image/name: prom-pushgateway
      image/version: 1.1.0
  template:
    metadata:
      namespace: ops
      name: prom-pushgateway
      labels:
        image/from: hub.docker.com
        image/name: prom-pushgateway
        image/version: 1.1.0
    spec:
      containers:
        - name: prom-pushgateway
          imagePullPolicy: IfNotPresent
          image: prom/pushgateway:v1.1.0
          ports:
            - name: http
              protocol: TCP
              containerPort: 9091
          resources:
            limits:
              memory: "1024Mi"
        - name: pushgateway-prune
          imagePullPolicy: IfNotPresent
          image: pushgateway-prune:latest
          env:
            - name: TTL
              value: "10"
            - name: PUSHGATEWAY_URL
              value: http://test
            - name: PUSH_WEBHOOK_URL
              value: https://test
```