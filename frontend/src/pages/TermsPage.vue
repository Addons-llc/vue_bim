<script setup>
// Text from "BIM TERMS AND CONDITIONS" (PDF). Values the document leaves as
// placeholders live here so they can be filled in one place.
// TODO: replace each "[Insert ...]" value before going live.
const TERMS_DETAILS = {
  subscriptionCancelCutoff: '[Insert Timeframe, e.g., 24 hours]',
  nonPerishableReturnDays: '[Insert Number]',
  jurisdiction: '[Insert Emirate, e.g., Dubai, UAE]',
  supportEmail: 'enquiry@addon-s.com',
  supportPhone: '+971 50 182 9977',
  address: 'Al Kitbi Building - No 4, Mezzanine Floor - Al Nahda St - Al Nahda First - Al Nahda - Dubai',
}

const d = TERMS_DETAILS
</script>

<template>
  <article class="terms-page">
    <header class="terms-head">
      <h1>Terms and Conditions</h1>
    </header>

    <section>
      <h2>1. Introduction and Acceptance of Terms</h2>
      <p>
        Welcome to Buy In Minutes. These Terms and Conditions ("Terms") govern your access to and
        use of the Buy In Minutes website (www.buyinminutes.com) and its associated mobile
        applications available on the App Store and Google Play. By accessing, browsing, or using
        our platform, you agree to be bound by these Terms.
      </p>
      <p>
        The platform is operated by ADDON-S LLC. If you do not agree to these Terms,
        you must not use our services.
      </p>
    </section>

    <section>
      <h2>2. Definitions</h2>
      <ul>
        <li><strong>"Platform"</strong> refers to the Buy In Minutes website and mobile applications.</li>
        <li>
          <strong>"Company," "We," "Us," or "Our"</strong> refers to Buy In Minutes and its parent
          entity, ADDON-S LLC.
        </li>
        <li>
          <strong>"User," "You," or "Your"</strong> refers to any individual or entity utilizing the
          Platform to purchase goods or services.
        </li>
        <li>
          <strong>"Products"</strong> refers to the goods available for purchase, including but not
          limited to food, fashion, printing &amp; stationary, frozen food, fresh vegetables, meat,
          fish, and groceries.
        </li>
        <li>
          <strong>"Vendor" or "Store"</strong> refers to the trusted nearby stores providing the
          actual goods and services listed on the Platform.
        </li>
      </ul>
    </section>

    <section>
      <h2>3. Products and Services</h2>
      <p>
        Buy In Minutes provides an e-commerce platform that allows users to purchase fresh
        vegetables, fruits, groceries, meat, fish, fashion items, and prepared food from nearby
        trusted stores. We act as an intermediary facilitating the transaction and delivery of these
        items. While we strive to ensure accurate product descriptions, we do not warrant that
        product descriptions, images, or other content are entirely accurate, complete, or
        error-free.
      </p>
    </section>

    <section>
      <h2>4. User Registration and Account Responsibilities</h2>
      <p>To make purchases, users may be required to register an account and log in. You agree to:</p>
      <ul>
        <li>Provide accurate, current, and complete information during registration.</li>
        <li>Safeguard your login credentials and immediately notify us of any unauthorized use.</li>
        <li>Allow location access to facilitate accurate delivery to select locations.</li>
      </ul>
    </section>

    <section>
      <h2>5. Orders and Order Processing</h2>
      <p>
        By placing an order, you are making an offer to purchase the selected Products. All orders
        are subject to acceptance by us and the respective Vendor. We reserve the right to cancel or
        refuse any order at our discretion (e.g., due to stock unavailability or pricing errors).
        Once an order is confirmed, you can utilize the "Track order" feature on our Platform.
      </p>
    </section>

    <section>
      <h2>6. Pricing and Payments</h2>
      <p>
        All prices listed on the Platform are in United Arab Emirates Dirham (AED). Prices are
        subject to change without notice. Payment must be made through the authorized payment
        methods available at checkout. By providing payment information, you represent and warrant
        that you are authorized to use the designated payment method.
      </p>
    </section>

    <section>
      <h2>7. Subscription Plans and Recurring Payments</h2>
      <p>
        We offer subscription-based products, such as the "Weekly Vegetable Kit" and "Weekly Basic
        Kit."
      </p>
      <ul>
        <li>
          <strong>Recurring Billing:</strong> By purchasing a subscription kit, you authorize ADDON-S
          LLC to initiate recurring payments (MOTO/recurring billing) automatically
          based on your selected billing cycle.
        </li>
        <li>
          <strong>Payment Authorization:</strong> Your selected payment method will be charged
          automatically prior to the delivery of each subscription cycle.
        </li>
      </ul>
    </section>

    <section>
      <h2>8. Automatic Renewal and Subscription Cancellation</h2>
      <ul>
        <li>
          <strong>Renewal:</strong> Subscription plans automatically renew at the end of each billing
          cycle unless canceled by the user.
        </li>
        <li>
          <strong>Cancellation:</strong> You may cancel your subscription at any time through your
          account settings or by contacting our Support team. Cancellations must be submitted at
          least {{ d.subscriptionCancelCutoff }} before the next scheduled billing date to avoid
          being charged for the upcoming cycle.
        </li>
      </ul>
    </section>

    <section>
      <h2>9. Refund and Cancellation Policy</h2>
      <ul>
        <li>
          <strong>Perishable Goods:</strong> Due to the nature of fresh items, frozen food, meat,
          fish, and prepared food, sales of perishable goods are generally final. Refunds or
          replacements will only be issued if items are delivered damaged, spoiled, or incorrect.
        </li>
        <li>
          <strong>Non-Perishable Goods:</strong> Returns or refunds for fashion items, printing
          &amp; stationary may be accepted within {{ d.nonPerishableReturnDays }} days of delivery,
          provided the items are unused and in their original packaging.
        </li>
        <li>
          <strong>Order Cancellation:</strong> Users may cancel standard orders before they are
          processed by the Vendor. Once an order is out for delivery, it cannot be canceled.
        </li>
      </ul>
    </section>

    <section>
      <h2>10. Delivery and Shipping Policy</h2>
      <p>
        Buy In Minutes aims to deliver products quickly from nearby trusted stores. Delivery times
        are estimates and not guaranteed. Users must ensure that location access is permitted on
        their device and browser, or manually select a correct delivery location, to ensure
        successful fulfillment.
      </p>
    </section>

    <section>
      <h2>11. User Responsibilities</h2>
      <p>
        You agree not to use the Platform for any unlawful purpose. You shall not interfere with the
        Platform's security features, attempt to gain unauthorized access to our network, or use the
        Platform to distribute malicious software or spam.
      </p>
    </section>

    <section>
      <h2>12. Privacy and Data Protection</h2>
      <p>
        Your privacy is important to us. By using the Platform, you consent to the collection, use,
        and sharing of your personal data as necessary to process orders, facilitate deliveries, and
        improve our Services. For full details, please review our separate
        <RouterLink :to="{ name: 'privacy-policy' }">Privacy Policy</RouterLink>.
      </p>
    </section>

    <section>
      <h2>13. Intellectual Property Rights</h2>
      <p>
        All content, trademarks, logos, images, and software on the Platform are the property of Buy
        In Minutes, ADDON-S LLC, or our Vendors. You may not reproduce, distribute, or
        create derivative works from any part of the Platform without explicit written permission.
      </p>
    </section>

    <section>
      <h2>14. Limitation of Liability</h2>
      <p>
        To the maximum extent permitted by law, ADDON-S LLC and Buy In Minutes shall
        not be liable for any indirect, incidental, special, or consequential damages arising from
        your use of the Platform or the Products purchased, including but not limited to health
        issues arising from food consumption or allergies.
      </p>
    </section>

    <section>
      <h2>15. Indemnification</h2>
      <p>
        You agree to indemnify and hold harmless Buy In Minutes, ADDON-S LLC, its
        affiliates, and employees from any claims, damages, liabilities, and expenses arising out of
        your breach of these Terms or your violation of any law or the rights of a third party.
      </p>
    </section>

    <section>
      <h2>16. Suspension and Termination</h2>
      <p>
        We reserve the right to suspend or terminate your account and access to the Platform at our
        sole discretion, without prior notice, if you violate these Terms or engage in fraudulent
        activities.
      </p>
    </section>

    <section>
      <h2>17. Changes to Terms &amp; Conditions</h2>
      <p>
        We may update these Terms periodically. Any changes will be posted on this page with an
        updated "Last Updated" date. Continued use of the Platform after such changes constitutes
        your acceptance of the revised Terms.
      </p>
    </section>

    <section>
      <h2>18. Governing Law and Jurisdiction</h2>
      <p>
        These Terms shall be governed by and construed in accordance with the laws of the United
        Arab Emirates. Any disputes arising in connection with these Terms shall be subject to the
        exclusive jurisdiction of the courts of {{ d.jurisdiction }}.
      </p>
    </section>

    <section>
      <h2>19. Contact Information</h2>
      <p>For support, tracking orders, or legal inquiries, please contact us at:</p>
      <ul>
        <li><strong>Company Entity:</strong> ADDON-S LLC</li>
        <li><strong>Email:</strong> <a :href="`mailto:${d.supportEmail}`">{{ d.supportEmail }}</a></li>
        <li>
          <strong>Phone:</strong>
          <a :href="`tel:${d.supportPhone.replace(/\s/g, '')}`">{{ d.supportPhone }}</a>
        </li>
        <li><strong>Address:</strong> {{ d.address }}</li>
      </ul>
    </section>
  </article>
</template>
