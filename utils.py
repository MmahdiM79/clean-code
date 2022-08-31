# JSONIC: the decorator
class jsonic(object):

    """ Relies on Python 2.7-ish string-encoding semantics; makes a whoooole lot
        of assumptions about naming, additional installed, apps, you name it –
        Also, it’s absolutely horrid. I hereby place it in the public domain.

        Usage example:

            class MyModel(models.Model):

                @jsonic(
                    skip=[
                        'categories', 'images', 'aximage_set', 'axflashmorsel_set',
                        'tags', 'tagstring', 'color', 'colors', 'topsat', 'complement', 'inversecomplement',
                    ], include=[
                        'keyimage', 'flashmorsel',
                    ],
                )
                def json(self, **kwargs):
                    return kwargs.get('json', None)

        … would then allow, on an instance `my_model` of model class `MyModel`,
          to call the method:

            >>> my_model.json()
            (… gigantic Python – not JSON! – dictionary …)

        … which in an API view the dict, which would have keys and values from
          the instance that vaguely corresponded to all the stuff in the decorator
          params, would get encoded and stuck in a response.

        Actual production code written by me, circa 2008. Yep.
    """

    def __init__(self, *decorargs, **deckeywords):
        self.deckeywords = deckeywords

    def __to_json(obj, **kwargs):
        
        thefields = obj._meta.get_all_field_names()
        kwargs.update(self.deckeywords)  # ??

        recurse = kwargs.get('recurse', 0)
        incl = kwargs.get('include')
        sk = kwargs.get('skip')
        if incl:
            if type(incl) == type([]):
                thefields.extend(incl)
            else:
                thefields.append(incl)
        if sk:
            if type(sk) == type([]):
                for skipper in sk:
                    if skipper in thefields:
                        thefields.remove(skipper)
            else:
                if sk in thefields:
                    thefields.remove(sk)

    @staticmethod
    def __first_vanilla_field(obj, dic, key, thedic, recurse_limit, thefields, **kwargs):
        for f in thefields:
            try:
                thedic = getattr(obj, "%s_set" % f)
            except AttributeError:
                try:
                    thedic = getattr(obj, f)
                except AttributeError: pass
                except ObjectDoesNotExist: pass
                else:
                    key = str(f)
            except ObjectDoesNotExist: pass
            else:
                key = "%s_set" % f

            if key:
                if hasattr(thedic, "__class__") and hasattr(thedic, "all"):
                    if callable(thedic.all):
                        if hasattr(thedic.all(), "json"):
                            if recurse < recurse_limit:
                                kwargs['recurse'] = recurse + 1
                                dic[key] = thedic.all().json(**kwargs)
                elif hasattr(thedic, "json"):
                    if recurse < recurse_limit:
                        kwargs['recurse'] = recurse + 1
                        dic[key] = thedic.json(**kwargs)
                else:
                    try:
                        theuni = thedic.__str__()
                    except UnicodeEncodeError:
                        theuni = thedic.encode('utf-8')
                    dic[key] = theuni

    @staticmethod
    def check_image_key(obj, dic):
        if hasattr(obj, "_ik"):
            if hasattr(obj, obj._ik.image_field):
                if hasattr(getattr(obj, obj._ik.image_field), 'size'):
                    if getattr(obj, obj._ik.image_field):
                        for ikaccessor in [getattr(obj, s.access_as) for s in obj._ik.specs]:
                            key = ikaccessor.spec.access_as
                            dic[key] = {
                                'url': ikaccessor.url,
                                'width': ikaccessor.width,
                                'height': ikaccessor.height,
                            }

    def __call__(self, fn):
        def jsoner(obj, **kwargs):
            dic = {}
            key = None
            thedic = None
            recurse_limit = 2
            
            thefields = self.__to_json(obj, **kwargs)

            # first vanilla fields
            self.__first_vanilla_field(obj, dic, key, thedic, recurse_limit, thefields, **kwargs)

            # now, do we have imagekit stuff in there?
            self.check_image_key(obj, dic)
            return fn(obj, json=dic, **kwargs)
        return jsoner


def reduce_tasks(regisyers, ids):
    for register in registers:
            if ids:  # Using optimized queries:
                objects = register.objects.filter(
                    id__in=ids).values_list("id", flat=True)
            else:
                objects = register.objects.all().values_list("id", flat=True)

            t = 0
            task_map = []

            # Defining method with a generator in a loop.
            def chunks(objects, length):
                for i in xrange(0, len(objects), length):
                    yield objects[i:i+length]

            for chunk in chunks(objects, 20):
                countdown = 5*t
                t += 1
                tasks_map.append(request_by_mapper(
                    register, chunk, countdown, datetime.now()))
        g = group(*tasks_map)
        reduce_task = chain(g, create_request_by_reduce_async.s(tasks_map))()
        

def create_payment_post(request):
    policy_id = request.POST.get('policy_id', '')
    currency = request.POST.get('currency')
    logger.debug(currency)
    policy = InsurancePolicy.objects.get(id=policy_id)
    try:
        payment = policy.payment_id
        # if payment is NULL then exeption
        payment.id
    except Exception as e:
        # everything is ok, new user
        # create payment with coinpayment
        post_params = {
            'amount': policy.fee,
            'currency1': 'BTC',
            'currency2': currency,
            'buyer_email':
                request.user.email,  # TODO set request.user.mail,
            'item_name': 'Policy for ' + policy.exchange.name,
            'item_number': policy.id
        }
        try:
            client = CryptoPayments(public_key, private_key)
            transaction = client.createTransaction(post_params)
            logger.debug(transaction)  # FOR DEBUG
            if len(transaction) == 0:
                raise Exception
        except Exception as e:
            logger.error(e)
            message = 'Payment gateway is down'
            responseData = {'error': True, 'message': message}
            return JsonResponse(responseData)
        

def new_user(currency, transaction):
    return UserPayments(
                status=0,
                update_date=datetime.datetime.now(),
                amount=transaction.amount,
                address=transaction.address,
                payment=transaction.txn_id,
                confirms_needed=transaction.confirms_needed,
                timeout=transaction.timeout,
                status_url=transaction.status_url,
                qrcode_url=transaction.qrcode_url,
                currency=currency)


def send_mail():
    default_email = os.environ.get(
                        'DJANGO_EMAIL_DEFAULT_EMAIL')
    subject = "Website: You’re one step away from being secured"
    message = render_to_string(
        'first_email.html', {'user': policy.user, 'payment': payment})
    send_mail(subject, message, default_email,
                [policy.user.email])
                